"""
Async Signal Exporter
Non-blocking signal export to OneX platform
"""

import logging
import os
import queue
import random
import threading
import time
from collections import deque
from typing import Any, Dict, List, Optional

import requests  # type: ignore[import-not-found]

logger = logging.getLogger(__name__)

# Max size for per-request sampling cache; evicts oldest when full
_SAMPLING_CACHE_MAX_SIZE = 10_000


class AsyncSignalExporter:
    """
    Asynchronous signal exporter
    Exports signals and request metadata in background threads to avoid blocking inference
    """

    def __init__(
        self,
        endpoint: str,
        api_key: Optional[str] = None,
        batch_size: int = 10,
        request_payload_endpoint: Optional[str] = None,
        request_response_endpoint: Optional[str] = None,
        sample_rate: float = 1.0,
        max_requests_per_minute: Optional[int] = None,
    ):
        self.endpoint = endpoint
        self.api_key = api_key
        self.batch_size = batch_size
        self.sample_rate = max(0.0, min(1.0, float(sample_rate)))
        self.max_requests_per_minute = (
            max(1, int(max_requests_per_minute)) if max_requests_per_minute is not None else None
        )

        self.container_id = self._detect_container_id()
        if self.container_id:
            logger.info("Signal exporter running in container %s", self.container_id)
        else:
            logger.info("Signal exporter could not detect a container identifier")

        self.request_payload_endpoint = (
            request_payload_endpoint or self._derive_related_endpoint(endpoint, "payload")
        )
        self.request_response_endpoint = (
            request_response_endpoint or self._derive_related_endpoint(endpoint, "response")
        )

        # Signal queue for async processing (thread-safe by design)
        self.signal_queue = queue.Queue(maxsize=1000)
        self.request_queue = queue.Queue(maxsize=500)

        # Thread synchronization for immediate wake-up and flush
        self._condition = threading.Condition()
        self._flush_requested = False
        self._pending_signals_count = 0

        # Per-request sampling: request_id -> True/False (sampled or not)
        # Evicted when full to bound memory in long-running processes
        self._sampling_decision: Dict[str, bool] = {}
        self._sampling_lock = threading.Lock()

        # Rate limit: timestamps of recent batch sends (for max_requests_per_minute)
        self._send_timestamps: deque = deque()
        self._rate_limit_lock = threading.Lock()

        # Track signals and responses per request_id
        # Maps request_id -> {
        #   "pending_count": int,  # Total signals for this request
        #   "exported_count": int,  # Successfully exported signals
        #   "response_event": Optional[Dict],  # Response to send after all signals exported
        # }
        self._request_tracking: Dict[str, Dict[str, Any]] = {}
        self._request_tracking_lock = threading.Lock()

        # Start background export threads
        self.running = True
        self.export_thread = threading.Thread(target=self._export_loop, daemon=True)
        self.export_thread.start()
        self.request_thread = threading.Thread(target=self._request_export_loop, daemon=True)
        self.request_thread.start()

        logger.info("Signal exporter initialized: %s", endpoint)
        if self.sample_rate < 1.0:
            logger.info("Sampling enabled: %.2f of requests will be exported", self.sample_rate)
        if self.max_requests_per_minute is not None:
            logger.info(
                "Throughput cap: at most %s batch requests per minute",
                self.max_requests_per_minute,
            )

    # --------------------------------------------------------------------- #
    # Signal export interface
    # --------------------------------------------------------------------- #

    def _should_sample_request(self, request_id: Optional[str]) -> bool:
        """
        Decide whether to sample this request (per-request sampling).
        Returns True to export, False to drop. Caches decision per request_id.
        """
        if request_id is None or self.sample_rate >= 1.0:
            return True
        with self._sampling_lock:
            if request_id in self._sampling_decision:
                return self._sampling_decision[request_id]
            # Evict oldest entries if cache is full (dict preserves insertion order in 3.7+)
            if len(self._sampling_decision) >= _SAMPLING_CACHE_MAX_SIZE:
                keys_to_remove = list(self._sampling_decision.keys())[
                    : _SAMPLING_CACHE_MAX_SIZE // 2
                ]
                for k in keys_to_remove:
                    del self._sampling_decision[k]
            sampled = random.random() < self.sample_rate
            self._sampling_decision[request_id] = sampled
            return sampled

    def export(self, signals: Dict[str, Any]):
        """
        Export signals asynchronously.
        Non-blocking - returns immediately.
        Thread-safe - can be called concurrently from multiple threads.
        When sample_rate < 1.0, only a fraction of requests are exported (per request_id).
        """
        try:
            payload = self._ensure_container_id(dict(signals))
            request_id = payload.get("request_id")

            # Per-request sampling: drop this request if not sampled
            if not self._should_sample_request(request_id):
                return

            # Track this signal if it has a request_id
            if request_id:
                with self._request_tracking_lock:
                    if request_id not in self._request_tracking:
                        self._request_tracking[request_id] = {
                            "pending_count": 0,
                            "exported_count": 0,
                            "response_event": None,
                        }
                    self._request_tracking[request_id]["pending_count"] += 1

            self.signal_queue.put_nowait(payload)

            # Wake up export thread immediately (thread-safe)
            with self._condition:
                self._pending_signals_count += 1
                self._condition.notify()  # Immediate wake-up, no timeout
        except queue.Full:
            logger.warning("Signal queue full, dropping signal")

    def export_request_payload(
        self,
        request_id: str,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Queue a request payload event for export."""
        event = {
            "type": "payload",
            "body": self._ensure_container_id(
                self._build_request_body("payload", request_id, payload, metadata)
            ),
        }
        self._enqueue_request_event(event)

    def export_request_response(
        self,
        request_id: str,
        response_payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Queue a request response event for export.
        The response will only be sent after all signals for this request_id are exported successfully.
        """
        event_body = self._ensure_container_id(
            self._build_request_body("response", request_id, response_payload, metadata)
        )
        
        # Track this response and check if we can send it immediately
        with self._request_tracking_lock:
            if request_id not in self._request_tracking:
                # No signals tracked for this request, send immediately
                self._request_tracking[request_id] = {
                    "pending_count": 0,
                    "exported_count": 0,
                    "response_event": None,
                }
                # Can send immediately - no signals to wait for
                self._post_json(self.request_response_endpoint, event_body, "request response")
            else:
                # Store response, will be sent when all signals are exported
                tracking = self._request_tracking[request_id]
                tracking["response_event"] = {
                    "body": event_body,
                }
                
                # Check if all signals are already exported successfully
                # If pending_count == exported_count, all signals have been exported
                if tracking["pending_count"] == tracking["exported_count"]:
                    # All signals already exported, send response now
                    self._post_json(
                        self.request_response_endpoint,
                        tracking["response_event"]["body"],
                        "request response"
                    )
                    tracking["response_event"] = None  # Clear after sending
                    # Clean up tracking and sampling cache
                    del self._request_tracking[request_id]
                    with self._sampling_lock:
                        self._sampling_decision.pop(request_id, None)

    # --------------------------------------------------------------------- #
    # Background loops
    # --------------------------------------------------------------------- #

    def _export_loop(self):
        """
        Background thread that exports batches of neural signals.
        Wakes up immediately when signals arrive (ZERO timeout delay).
        Sends signals immediately upon arrival, regardless of batch size.
        Thread-safe for concurrent signal exports.
        """
        batch: List[Dict[str, Any]] = []

        while self.running or not self.signal_queue.empty():
            try:
                # Collect ALL available signals immediately (non-blocking)
                # This efficiently handles concurrent signals arriving simultaneously
                signals_collected = False
                while True:
                    try:
                        signal = self.signal_queue.get_nowait()
                        batch.append(self._ensure_container_id(signal))
                        signals_collected = True
                    except queue.Empty:
                        break
                
                # Send signals immediately if we collected any (no delay, no waiting for batch_size)
                if signals_collected and batch:
                    self._send_batch(batch)
                    batch = []
                
                # Check if flush was requested (thread-safe)
                flush_needed = False
                pending_batch_for_flush = None
                with self._condition:
                    flush_needed = self._flush_requested
                    if flush_needed:
                        self._flush_requested = False
                        # Send any pending batch if flush requested
                        if batch:
                            # Release lock before sending to avoid holding it during I/O
                            pending_batch_for_flush = batch
                            batch = []
                    self._pending_signals_count = 0
                
                # Send batch if flush was requested
                if pending_batch_for_flush:
                    self._send_batch(pending_batch_for_flush)
                
                # Wait for new signals ONLY if we didn't collect any and we're still running
                if not signals_collected:
                    with self._condition:
                        # Double-check queue is still empty and we should keep running
                        if not self.running and self.signal_queue.empty():
                            break
                        # Wait until notified - this wakes IMMEDIATELY when export() calls notify()
                        # NO TIMEOUT - waits indefinitely until woken
                        self._condition.wait()
                        # After waking, loop immediately checks queue again (no delay)
                    
            except Exception as exc:
                logger.error("Error in signal export loop: %s", exc)

        # Final flush of any remaining signals
        if batch:
            self._send_batch(batch)

    def _request_export_loop(self):
        """Background thread that exports request payloads/responses."""
        while self.running or not self.request_queue.empty():
            try:
                event = self.request_queue.get(timeout=1.0)
                event_type = event.get("type")
                body = self._ensure_container_id(event.get("body", {}))

                if event_type == "payload":
                    self._post_json(self.request_payload_endpoint, body, "request payload")
                elif event_type == "response":
                    self._post_json(self.request_response_endpoint, body, "request response")
                else:
                    logger.warning("Unknown request queue event type: %s", event_type)
            except queue.Empty:
                continue
            except Exception as exc:
                logger.error("Error exporting request data: %s", exc)

    # --------------------------------------------------------------------- #
    # HTTP helpers
    # --------------------------------------------------------------------- #

    def _wait_for_rate_limit(self):
        """
        If max_requests_per_minute is set, wait until we are under the limit
        (sliding window of last 60 seconds). Call before sending a batch.
        """
        if self.max_requests_per_minute is None:
            return
        with self._rate_limit_lock:
            now = time.time()
            cutoff = now - 60.0
            while self._send_timestamps and self._send_timestamps[0] < cutoff:
                self._send_timestamps.popleft()
            while len(self._send_timestamps) >= self.max_requests_per_minute:
                sleep_until = self._send_timestamps[0] + 60.0
                sleep_time = sleep_until - time.time()
                if sleep_time > 0:
                    # Release lock while sleeping so other threads can proceed
                    self._rate_limit_lock.release()
                    try:
                        time.sleep(sleep_time)
                    finally:
                        self._rate_limit_lock.acquire()
                now = time.time()
                cutoff = now - 60.0
                while self._send_timestamps and self._send_timestamps[0] < cutoff:
                    self._send_timestamps.popleft()

    def _record_send(self):
        """Record a successful batch send for rate limiting. Call after a successful POST."""
        if self.max_requests_per_minute is None:
            return
        with self._rate_limit_lock:
            self._send_timestamps.append(time.time())

    def _send_batch(self, batch: list[Dict[str, Any]]):
        """
        Send batch of signals to OneX API.
        Tracks successful exports and sends response payloads when all signals for a request are exported.
        Respects max_requests_per_minute when set.
        """
        try:
            self._wait_for_rate_limit()

            headers: Dict[str, str] = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            sanitized_batch = [self._ensure_container_id(item) for item in batch]

            for index, payload in enumerate(sanitized_batch):
                logger.info(
                    "Preparing to export signal #%s (container_id=%s, type=%s, forward_pass_index=%s)",
                    index,
                    payload.get("container_id"),
                    payload.get("signal_type"),
                    payload.get("forward_pass_index", "N/A"),
                )

            response = requests.post(
                self.endpoint,
                json={"signals": sanitized_batch},
                headers=headers,
                timeout=None,  # Infinite timeout - wait as long as server responds
            )

            if 200 <= response.status_code < 300:
                self._record_send()
                logger.info("Exported %s signals successfully", len(batch))

                # Track successful exports per request_id and send responses if ready
                self._handle_successful_export(sanitized_batch)
            else:
                logger.warning("Signal export failed: %s", response.status_code)

        except Exception as exc:
            logger.error("Failed to export signals: %s", exc)
    
    def _handle_successful_export(self, batch: list[Dict[str, Any]]):
        """
        Handle successful signal export by tracking exported signals per request_id.
        If all signals for a request_id are exported, send the response payload.
        """
        # Count signals per request_id in this batch
        request_id_counts: Dict[str, int] = {}
        for signal in batch:
            request_id = signal.get("request_id")
            if request_id:
                request_id_counts[request_id] = request_id_counts.get(request_id, 0) + 1
        
        # Update tracking and send responses if ready
        responses_to_send = []
        
        with self._request_tracking_lock:
            for request_id, count in request_id_counts.items():
                if request_id in self._request_tracking:
                    tracking = self._request_tracking[request_id]
                    tracking["exported_count"] += count
                    
                    # Check if all signals for this request are exported and response is waiting
                    if (tracking["pending_count"] == tracking["exported_count"] and 
                        tracking["response_event"] is not None):
                        # All signals exported, queue response to send
                        responses_to_send.append((request_id, tracking["response_event"]["body"]))
                        tracking["response_event"] = None  # Clear after queuing
                        # Clean up tracking and sampling cache
                        del self._request_tracking[request_id]
                        with self._sampling_lock:
                            self._sampling_decision.pop(request_id, None)
        
        # Send responses outside the lock to avoid holding it during I/O
        for request_id, response_body in responses_to_send:
            self._post_json(
                self.request_response_endpoint,
                response_body,
                f"request response for request_id {request_id}"
            )

    def _post_json(self, endpoint: str, body: Dict[str, Any], description: str):
        try:
            headers: Dict[str, str] = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            response = requests.post(endpoint, json=body, headers=headers, timeout=None)  # Infinite timeout - wait as long as server responds
            if 200 <= response.status_code < 300:
                logger.info("Exported %s successfully", description)
            else:
                logger.warning("Exporting %s failed: %s", description, response.status_code)
        except Exception as exc:
            logger.error("Failed to export %s: %s", description, exc)

    # --------------------------------------------------------------------- #
    # Public lifecycle
    # --------------------------------------------------------------------- #

    def flush(self):
        """
        Flush any pending signals immediately.
        Non-blocking - triggers immediate export of pending batch.
        Thread-safe - can be called concurrently.
        """
        with self._condition:
            self._flush_requested = True
            self._condition.notify()  # Wake up export thread immediately
        logger.debug("Flush requested - pending signals will be exported immediately")

    def close(self):
        """Stop exporter and cleanup."""
        # Flush any pending signals before closing
        self.flush()
        self.running = False
        self.export_thread.join(timeout=5.0)
        self.request_thread.join(timeout=5.0)
        logger.info("Signal exporter stopped")

    # --------------------------------------------------------------------- #
    # Utility helpers
    # --------------------------------------------------------------------- #

    def _detect_container_id(self) -> Optional[str]:
        """Attempt to detect the container identifier (if running in Docker)."""
        hostname = os.environ.get("HOSTNAME")
        if hostname and len(hostname) >= 6:
            logger.debug("Detected container ID from HOSTNAME: %s", hostname)
            return hostname

        try:
            with open("/proc/self/cgroup", "r", encoding="utf-8") as cgroup_file:
                for line in cgroup_file:
                    parts = line.strip().split("/")
                    if parts and parts[-1]:
                        candidate = parts[-1]
                        if len(candidate) >= 6:
                            logger.debug("Detected container ID from cgroup: %s", candidate)
                            return candidate
        except OSError:
            logger.debug(
                "Unable to read /proc/self/cgroup for container ID detection",
                exc_info=True,
            )

        logger.debug("Container ID could not be detected")
        return None

    def _ensure_container_id(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Guarantee that each payload has the detected container identifier."""
        if self.container_id:
            payload["container_id"] = self.container_id
        return payload

    def _enqueue_request_event(self, event: Dict[str, Any]):
        try:
            self.request_queue.put_nowait(event)
        except queue.Full:
            logger.warning("Request queue full, dropping event")

    def _derive_related_endpoint(self, signals_endpoint: str, suffix: str) -> str:
        """
        Derive the related request endpoint from the signals endpoint.

        Example:
            signals endpoint: http://host/api/signals/batch
            derived payload:  http://host/api/requests/payload
        """
        base = signals_endpoint
        if "/signals" in signals_endpoint:
            base = signals_endpoint.split("/signals", 1)[0]
        return f"{base}/requests/{suffix}"

    def _build_request_body(
        self,
        field_name: str,
        request_id: str,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "request_id": request_id,
            "timestamp": time.time(),
            "metadata": metadata or {},
        }
        if self.container_id:
            body["container_id"] = self.container_id
        body[field_name] = payload
        return body
