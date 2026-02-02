"""
PyTorch Adapter
Captures neural signals from PyTorch models
"""

from __future__ import annotations

import logging
import time
import threading
import uuid
from functools import wraps
from typing import Any, Dict, Iterable, List, Mapping, Optional

import numpy as np  # type: ignore[import-not-found]

from onex.utils.assessment_config import filter_signal_by_assessments

try:  # pragma: no cover - optional dependency
    import torch  # type: ignore[import-not-found]
    import torch.nn as nn  # type: ignore[import-not-found]
except Exception as exc:  # pragma: no cover - optional dependency
    torch = None  # type: ignore[assignment]
    nn = None  # type: ignore[assignment]
    _TORCH_IMPORT_ERROR: Optional[Exception] = exc
else:
    _TORCH_IMPORT_ERROR = None

logger = logging.getLogger(__name__)


class PyTorchAdapter:
    """
    PyTorch-specific signal capture adapter
    Automatically hooks into BERT and other transformer models
    """
    
    def __init__(self, exporter, config: Dict[str, Any]):
        if torch is None:
            raise RuntimeError(
                "PyTorch is not installed. Install the 'pytorch' extra to enable "
                "PyTorch monitoring, e.g. pip install onex-sdk[pytorch]"
            ) from _TORCH_IMPORT_ERROR

        self.exporter = exporter
        self.config = config or {}
        self.hooks = []

        # Sampling configuration for exported signals
        batch_value = self.config.get("hidden_state_sample_batch", 1)
        tokens_value = self.config.get("hidden_state_sample_tokens", 4)
        features_value = self.config.get("hidden_state_sample_features", 32)
        precision_value = self.config.get("hidden_state_precision", 6)

        self.sample_batch_size = max(1, int(batch_value or 1))
        self.sample_tokens = max(1, int(tokens_value or 4))
        self.sample_features = max(1, int(features_value or 32))
        self.embedding_precision = int(precision_value) if precision_value is not None else -1
        self.capture_full_hidden_state = bool(self.config.get("capture_full_hidden_state", False))
        self._request_local = threading.local()
        self.payload_max_items = max(1, int(self.config.get("payload_sample_items", 5)))
        self.payload_tensor_elements = max(1, int(self.config.get("payload_tensor_sample", 32)))
        self.payload_max_depth = max(0, int(self.config.get("payload_max_depth", 2)))
        metadata_config = self.config.get("request_metadata", {})
        self.request_metadata = metadata_config if isinstance(metadata_config, dict) else {}
        self.capture_request_payload = self.config.get("capture_request_payload", True)
        self.capture_response_payload = self.config.get("capture_response_payload", True)

        # Logits / probabilities capture (for Uncertainty, Calibration, Confidence assessments).
        # Default False when not set; only explicit True enables capture.
        self.capture_logits = self.config.get("capture_logits", False) is True
        self.capture_probabilities = self.config.get("capture_probabilities", False) is True
        self.logits_sample_size = max(1, int(self.config.get("logits_sample_size", 64)))

        # Assessment configuration - which assessments are enabled
        assessments = self.config.get("assessments", [])
        self.enabled_assessments = assessments if isinstance(assessments, list) else []
        
        # Track which request_ids have already exported their payload and response
        # This prevents duplicate exports when forward() is called multiple times
        # (e.g., during GPT text generation where forward is called per token)
        # Using thread-local storage to avoid race conditions
        self._exported_request_payloads_lock = threading.Lock()
        self._exported_request_payloads: set = set()
        self._exported_request_responses_lock = threading.Lock()
        self._exported_request_responses: set = set()
    
    def _export_signal(self, signals: Dict[str, Any]):
        """
        Export signal with assessment-based filtering applied.
        Only includes fields required by enabled assessments.
        """
        if self.enabled_assessments:
            filtered_signals = filter_signal_by_assessments(signals, self.enabled_assessments)
            self.exporter.export(filtered_signals)
        else:
            # No assessments enabled, export full signal (backward compatibility)
            self.exporter.export(signals)
        
    def attach_monitoring(self, model):
        """Attach monitoring hooks to PyTorch model"""
        
        # Detect model type
        model_type = self._detect_model_type(model)
        logger.info(f"Detected model type: {model_type}")
        
        # Attach appropriate hooks based on model type
        if 'bert' in model_type.lower():
            self._attach_bert_hooks(model)
        elif 'gpt' in model_type.lower():
            self._attach_gpt_hooks(model)
        elif 'vit' in model_type.lower() or 'vision' in model_type.lower():
            self._attach_vit_hooks(model)
        else:
            self._attach_generic_hooks(model)

        self._wrap_model_forward(model)
        
        logger.info(f"Attached {len(self.hooks)} monitoring hooks")
        
        return model
    
    def _detect_model_type(self, model) -> str:
        """Detect specific model architecture"""
        model_name = model.__class__.__name__.lower()
        
        if hasattr(model, 'config'):
            model_type = getattr(model.config, 'model_type', model_name)
            # Also check model_type in config for ViT
            if 'vit' in model_type.lower() or 'vision' in model_type.lower():
                return model_type
            # Check class name for ViT
            if 'vit' in model_name or 'vision' in model_name:
                return model_type if model_type else 'vit'
            return model_type
        
        # Fallback: check class name
        if 'vit' in model_name or 'vision' in model_name:
            return 'vit'
        
        return model_name
    
    def _attach_bert_hooks(self, model):
        """Attach BERT-specific monitoring hooks"""
        logger.info("Attaching BERT-specific hooks")
        
        # Hook 1: Capture hidden states from each encoder layer
        if hasattr(model, 'bert') and hasattr(model.bert, 'encoder'):
            total_layers = len(model.bert.encoder.layer)
            for layer_idx, layer in enumerate(model.bert.encoder.layer):
                # Get module name if available
                module_name = None
                for name, module in model.named_modules():
                    if module is layer:
                        module_name = name
                        break
                hook = layer.register_forward_hook(
                    self._create_layer_hook(layer_idx, 'bert_encoder', module_name, total_layers)
                )
                self.hooks.append(hook)
                logger.info(f"Hooked encoder layer: {layer}")
                logger.info(f"Hooked encoder layer: {hook}")
        
        # Hook 2: Capture attention patterns
        if hasattr(model, 'bert') and hasattr(model.bert, 'encoder'):
            total_layers = len(model.bert.encoder.layer)
            for layer_idx, layer in enumerate(model.bert.encoder.layer):
                attention = layer.attention.self
                # Get module name if available
                attention_module_name = None
                for name, module in model.named_modules():
                    if module is attention:
                        attention_module_name = name
                        break
                hook = attention.register_forward_hook(
                    self._create_attention_hook(layer_idx, attention_module_name, total_layers)
                )
                logger.info(f"Hooked attention layer: {attention}")
                logger.info(f"Hooked attention layer: {hook}")
                self.hooks.append(hook)
        
        # Hook 2b: Capture embedding outputs
        if hasattr(model, 'bert') and hasattr(model.bert, 'embeddings'):
            hook = model.bert.embeddings.register_forward_hook(
                self._create_embedding_hook('bert_embeddings')
            )
            logger.info(f"Hooked embedding layer: {model.bert.embeddings}")
            logger.info(f"Hooked embedding layer: {hook}")
            self.hooks.append(hook)

        # Hook 3: Capture pre-classification embeddings (KEY SIGNAL!)
        for name, module in model.named_modules():
            if 'classifier' in name.lower() or 'head' in name.lower():
                hook = module.register_forward_hook(
                    self._create_classification_hook(name)
                )
                self.hooks.append(hook)
                logger.info(f"Hooked classification layer: {name}")
    
    def _attach_gpt_hooks(self, model):
        """Attach GPT-specific monitoring hooks"""
        logger.info("Attaching GPT-specific hooks")

        # Hook transformer blocks (hidden states)
        if hasattr(model, 'transformer') and hasattr(model.transformer, 'h'):
            total_layers = len(model.transformer.h)
            for layer_idx, layer in enumerate(model.transformer.h):
                # Get module name if available
                module_name = None
                for name, module in model.named_modules():
                    if module is layer:
                        module_name = name
                        break
                hook = layer.register_forward_hook(
                    self._create_layer_hook(layer_idx, 'gpt_block', module_name, total_layers)
                )
                self.hooks.append(hook)

            # Hook attention in each GPT block (GPT-2: transformer.h[i].attn)
            # GPT2Attention returns (attn_output, present, attn_weights) when output_attentions=True
            for layer_idx, layer in enumerate(model.transformer.h):
                attn = getattr(layer, 'attn', None)
                if attn is None:
                    continue
                attn_module_name = None
                for name, module in model.named_modules():
                    if module is attn:
                        attn_module_name = name
                        break
                hook = attn.register_forward_hook(
                    self._create_attention_hook(
                        layer_idx,
                        module_name=attn_module_name,
                        total_layers=total_layers,
                        attention_output_index=2,  # GPT: (attn_output, present, attn_weights)
                    )
                )
                self.hooks.append(hook)
                logger.info("Hooked GPT attention layer %s: %s", layer_idx, attn)
    
    def _attach_vit_hooks(self, model):
        """Attach Vision Transformer (ViT) specific monitoring hooks"""
        logger.info("Attaching ViT-specific hooks")
        
        # Hook 1: Capture hidden states from each encoder layer
        if hasattr(model, 'vit') and hasattr(model.vit, 'encoder'):
            total_layers = len(model.vit.encoder.layer)
            for layer_idx, layer in enumerate(model.vit.encoder.layer):
                # Get module name if available
                module_name = None
                for name, module in model.named_modules():
                    if module is layer:
                        module_name = name
                        break
                hook = layer.register_forward_hook(
                    self._create_layer_hook(layer_idx, 'vit_encoder', module_name, total_layers)
                )
                self.hooks.append(hook)
                logger.info(f"Hooked ViT encoder layer: {layer}")
        elif hasattr(model, 'encoder'):
            # Some ViT models have encoder directly on model
            if hasattr(model.encoder, 'layer'):
                total_layers = len(model.encoder.layer)
                for layer_idx, layer in enumerate(model.encoder.layer):
                    # Get module name if available
                    module_name = None
                    for name, module in model.named_modules():
                        if module is layer:
                            module_name = name
                            break
                    hook = layer.register_forward_hook(
                        self._create_layer_hook(layer_idx, 'vit_encoder', module_name, total_layers)
                    )
                    self.hooks.append(hook)
                    logger.info(f"Hooked ViT encoder layer: {layer}")
        
        # Hook 2: Capture attention patterns
        if hasattr(model, 'vit') and hasattr(model.vit, 'encoder'):
            for layer_idx, layer in enumerate(model.vit.encoder.layer):
                if hasattr(layer, 'attention') and hasattr(layer.attention, 'self'):
                    attention = layer.attention.self
                    hook = attention.register_forward_hook(
                        self._create_attention_hook(layer_idx)
                    )
                    logger.info(f"Hooked ViT attention layer: {attention}")
                    self.hooks.append(hook)
        elif hasattr(model, 'encoder') and hasattr(model.encoder, 'layer'):
            for layer_idx, layer in enumerate(model.encoder.layer):
                if hasattr(layer, 'attention') and hasattr(layer.attention, 'self'):
                    attention = layer.attention.self
                    hook = attention.register_forward_hook(
                        self._create_attention_hook(layer_idx)
                    )
                    logger.info(f"Hooked ViT attention layer: {attention}")
                    self.hooks.append(hook)
        
        # Hook 3: Capture final model output to extract CLS token embedding
        # This is the KEY signal for ViT models - the CLS token at index 0
        hook = model.register_forward_hook(self._create_vit_output_hook())
        self.hooks.append(hook)
        logger.info("Hooked ViT model output for CLS token extraction")
        
        # Hook 4: Capture pre-classification embeddings (if classifier/head exists)
        for name, module in model.named_modules():
            if 'classifier' in name.lower() or 'head' in name.lower():
                hook = module.register_forward_hook(
                    self._create_classification_hook(name)
                )
                self.hooks.append(hook)
                logger.info(f"Hooked ViT classification layer: {name}")
    
    def _attach_generic_hooks(self, model):
        """Attach generic hooks for unknown models"""
        logger.info("Attaching generic hooks")
        
        # Hook all Linear and LayerNorm layers
        for name, module in model.named_modules():
            if isinstance(module, (nn.Linear, nn.LayerNorm)):
                hook = module.register_forward_hook(
                    self._create_generic_hook(name)
                )
                self.hooks.append(hook)
            elif isinstance(module, nn.Embedding):
                hook = module.register_forward_hook(
                    self._create_embedding_hook(name)
                )
                self.hooks.append(hook)
    
    def _create_layer_hook(self, layer_idx: int, layer_type: str, module_name: Optional[str] = None, total_layers: Optional[int] = None):
        """Create hook for capturing layer outputs"""
        def hook(module, input, output):
            try:
                # Extract hidden states
                if isinstance(output, tuple):
                    hidden_state = output[0]
                else:
                    hidden_state = output

                hidden_tensor = self._prepare_tensor(hidden_state)
                if hidden_tensor is None:
                    return

                cls_info = self._collect_cls_embeddings(hidden_tensor)

                # Signal #1 & #2: Token states and CLS embedding
                signal_type = f"hidden_states.{layer_type}.layer_{layer_idx}"
                forward_pass_index = self._get_forward_pass_index()
                signals = {
                    'framework': 'pytorch',
                    'signal_type': signal_type,
                    'layer_type': layer_type,
                    'layer_index': layer_idx,
                    'forward_pass_index': forward_pass_index,  # Distinguishes multiple forward passes during generation
                    'timestamp': time.time(),
                    'request_id': self._get_request_id(),
                    'statistics': self._compute_tensor_statistics(hidden_tensor),
                    'neural_health': self._compute_neural_health(hidden_tensor),
                    'hidden_state_sample': self._sample_hidden_state(hidden_tensor),
                    'token_statistics': self._compute_token_statistics(hidden_tensor),
                    'feature_statistics': self._compute_feature_statistics(hidden_tensor),
                    'token_norms': self._compute_token_norms(hidden_tensor),
                    'pooled_embedding': self._compute_pooled_embeddings(hidden_tensor),
                    'hidden_state_energy': self._compute_hidden_state_energy(hidden_tensor),
                    'cls_embedding': cls_info.get('primary', []),
                    'cls_embedding_batch': cls_info.get('batch', []),
                    'cls_embedding_norms': cls_info.get('norms', []),
                    'cls_embedding_stats': cls_info.get('statistics', {}),
                }
                
                # Add additional distinguishing information
                if module_name is not None:
                    signals['module_name'] = module_name
                    signals['module_class'] = module.__class__.__name__
                if total_layers is not None:
                    signals['total_layers'] = total_layers
                    signals['layer_position'] = f"{layer_idx + 1}/{total_layers}"  # 1-indexed for readability

                if self.capture_full_hidden_state:
                    signals['hidden_state_full'] = hidden_tensor.tolist()

                logger.info(
                    "Hidden layer %s (%s) statistics: %s",
                    layer_idx,
                    layer_type,
                    signals["statistics"],
                )
                logger.info(
                    "Hidden layer %s (%s) neural health: %s",
                    layer_idx,
                    layer_type,
                    signals["neural_health"],
                )

                # Export asynchronously (with assessment filtering if enabled)
                self._export_signal(signals)

            except Exception as e:
                logger.error(f"Error in layer hook: {e}")
        
        return hook
    
    def _create_attention_hook(
        self,
        layer_idx: int,
        module_name: Optional[str] = None,
        total_layers: Optional[int] = None,
        attention_output_index: int = 1,
    ):
        """
        Create hook for capturing attention patterns.
        BERT/ViT return (context, attention_weights) -> index 1.
        GPT-2 returns (attn_output, present, attention_weights) -> index 2.
        """
        # Capture variables in closure
        captured_module_name = module_name
        captured_total_layers = total_layers
        captured_layer_idx = layer_idx
        captured_index = attention_output_index

        def hook(module, input, output):
            try:
                # Extract attention weights: GPT uses index 2, BERT/ViT use index 1
                attention_weights = None
                if isinstance(output, tuple) and len(output) > captured_index:
                    candidate = output[captured_index]
                    if isinstance(candidate, torch.Tensor):
                        attention_weights = candidate
                if attention_weights is None and isinstance(output, tuple) and len(output) > 1:
                    candidate = output[1]
                    if isinstance(candidate, torch.Tensor):
                        attention_weights = candidate

                if attention_weights is not None:
                    # Signal #3: Attention patterns
                    signal_type = f"attention.layer_{captured_layer_idx}"
                    forward_pass_index = self._get_forward_pass_index()
                    signals = {
                        'framework': 'pytorch',
                        'signal_type': signal_type,
                        'layer_index': captured_layer_idx,
                        'forward_pass_index': forward_pass_index,  # Distinguishes multiple forward passes during generation
                        'timestamp': time.time(),
                        'request_id': self._get_request_id(),
                        # Attention metrics
                        'attention_metrics': {
                            'entropy_per_head': self._compute_attention_entropy(attention_weights),
                            'max_attention': float(attention_weights.max()),
                            'mean_attention': float(attention_weights.mean()),
                            'head_agreement': float(attention_weights.std(dim=1).mean())
                        },
                        # Shape information
                        'shape': list(attention_weights.shape),
                        'num_heads': attention_weights.shape[1]
                    }
                    if captured_module_name is not None:
                        signals['module_name'] = captured_module_name
                        signals['module_class'] = module.__class__.__name__
                    if captured_total_layers is not None:
                        signals['total_layers'] = captured_total_layers
                        signals['layer_position'] = f"{captured_layer_idx + 1}/{captured_total_layers}"  # 1-indexed for readability
                    logger.info(
                        "Attention layer %s metrics: %s",
                        layer_idx,
                        signals["attention_metrics"],
                    )
                    logger.info(
                        "Attention layer %s shape: %s",
                        layer_idx,
                        signals["shape"],
                    )
                    self._export_signal(signals)
            
            except Exception as e:
                logger.error(f"Error in attention hook: {e}")
        
        return hook
    
    def _create_classification_hook(self, layer_name: str):
        """Create hook for pre-classification embeddings (PRIMARY SIGNAL)"""
        def hook(module, input, output):
            try:
                # This is the KEY signal for domain detection!
                cls_embedding = input[0].detach().cpu()
                
                signal_type = f"pre_classification.{layer_name}"
                forward_pass_index = self._get_forward_pass_index()
                signals = {
                    'framework': 'pytorch',
                    'signal_type': signal_type,
                    'layer_name': layer_name,
                    'forward_pass_index': forward_pass_index,  # Distinguishes multiple forward passes during generation
                    'timestamp': time.time(),
                    'request_id': self._get_request_id(),
                    
                    # Raw embedding vector (768-dim for BERT-base)
                    'embedding': cls_embedding.numpy().tolist(),
                    
                    # Comprehensive statistics
                    'statistics': {
                        'mean': float(cls_embedding.mean()),
                        'std': float(cls_embedding.std()),
                        'norm': float(torch.norm(cls_embedding)),
                        'max': float(cls_embedding.max()),
                        'min': float(cls_embedding.min())
                    },
                    
                    # Neural health indicators
                    'neural_health': {
                        'sparsity': float((cls_embedding == 0).float().mean()),
                        'saturation': float((torch.abs(cls_embedding) > 0.95).float().mean()),
                        'stability': self._compute_stability(cls_embedding)
                    },
                    
                    # Domain detection indicators
                    'domain_indicators': {
                        'magnitude': float(torch.norm(cls_embedding)),
                        'information_density': float((cls_embedding != 0).float().mean()),
                        'preliminary_ood_score': self._quick_ood_estimate(cls_embedding)
                    }
                }
                
                logger.info(
                    "Pre-classification layer %s statistics: %s",
                    layer_name,
                    signals["statistics"],
                )
                logger.info(
                    "Pre-classification layer %s neural health: %s",
                    layer_name,
                    signals["neural_health"],
                )
                logger.info(
                    "Pre-classification layer %s domain indicators: %s",
                    layer_name,
                    signals["domain_indicators"],
                )

                self._export_signal(signals)
            
            except Exception as e:
                logger.error(f"Error in classification hook: {e}")
        
        return hook
    
    def _create_vit_output_hook(self):
        """Create hook for capturing ViT model output and extracting CLS token embedding"""
        def hook(module, input, output):
            try:
                # ViT models typically return BaseModelOutputWithPooling or similar
                # Extract last_hidden_state or pooler_output
                last_hidden_state = None
                pooler_output = None
                
                # Handle different output formats
                # First check if it's a BaseModelOutput-like object (has attributes)
                if hasattr(output, 'last_hidden_state'):
                    last_hidden_state = output.last_hidden_state
                    pooler_output = getattr(output, 'pooler_output', None)
                elif isinstance(output, tuple):
                    # Assume first element is last_hidden_state
                    last_hidden_state = output[0] if len(output) > 0 else None
                    pooler_output = output[1] if len(output) > 1 else None
                else:
                    # Assume output is the hidden state directly
                    last_hidden_state = output
                
                if last_hidden_state is None:
                    return
                
                hidden_tensor = self._prepare_tensor(last_hidden_state)
                if hidden_tensor is None:
                    return
                
                # Extract CLS token embedding (index 0 in sequence dimension)
                # Shape: [batch_size, num_patches+1, hidden_size] or [num_patches+1, hidden_size]
                # CLS token is at index 0 in the sequence dimension
                cls_embedding = None
                if hidden_tensor.dim() == 3:
                    # 3D: [batch_size, num_patches+1, hidden_size]
                    # Get CLS token (first token in sequence) for first batch item
                    cls_embedding = hidden_tensor[0, 0, :]  # [hidden_size]
                elif hidden_tensor.dim() == 2:
                    # 2D: [num_patches+1, hidden_size] (single batch or no batch dimension)
                    cls_embedding = hidden_tensor[0, :]  # [hidden_size]
                elif hidden_tensor.dim() == 1:
                    # 1D: already a single embedding vector
                    cls_embedding = hidden_tensor
                
                # Prefer pooler_output if available (it's the processed CLS embedding)
                if pooler_output is not None:
                    pooler_tensor = self._prepare_tensor(pooler_output)
                    if pooler_tensor is not None:
                        if pooler_tensor.dim() >= 2:
                            cls_embedding = pooler_tensor[0]  # Get first batch item
                        else:
                            cls_embedding = pooler_tensor
                
                if cls_embedding is None:
                    return
                
                # Create signal with embedding field (will be normalized to embedding_vector by assessment config)
                signal_type = "pre_classification.vit_output"
                forward_pass_index = self._get_forward_pass_index()
                signals = {
                    'framework': 'pytorch',
                    'signal_type': signal_type,
                    'layer_name': 'vit_output',
                    'forward_pass_index': forward_pass_index,  # Distinguishes multiple forward passes during generation
                    'timestamp': time.time(),
                    'request_id': self._get_request_id(),
                    
                    # Raw embedding vector (CLS token embedding)
                    'embedding': cls_embedding.numpy().tolist(),
                    
                    # Comprehensive statistics
                    'statistics': {
                        'mean': float(cls_embedding.mean()),
                        'std': float(cls_embedding.std()),
                        'norm': float(torch.norm(cls_embedding)),
                        'max': float(cls_embedding.max()),
                        'min': float(cls_embedding.min())
                    },
                    
                    # Neural health indicators
                    'neural_health': {
                        'sparsity': float((cls_embedding == 0).float().mean()),
                        'saturation': float((torch.abs(cls_embedding) > 0.95).float().mean()),
                        'stability': self._compute_stability(cls_embedding)
                    },
                    
                    # Domain detection indicators
                    'domain_indicators': {
                        'magnitude': float(torch.norm(cls_embedding)),
                        'information_density': float((cls_embedding != 0).float().mean()),
                        'preliminary_ood_score': self._quick_ood_estimate(cls_embedding)
                    },
                    
                    # Also include CLS embedding in the format expected by assessment config
                    'cls_embedding': [cls_embedding.numpy().tolist()],
                    'pooled_embedding': [cls_embedding.numpy().tolist()],
                }
                
                logger.info(
                    "ViT output CLS embedding statistics: %s",
                    signals["statistics"],
                )
                logger.info(
                    "ViT output CLS embedding neural health: %s",
                    signals["neural_health"],
                )
                logger.info(
                    "ViT output CLS embedding domain indicators: %s",
                    signals["domain_indicators"],
                )

                self._export_signal(signals)
            
            except Exception as e:
                logger.error(f"Error in ViT output hook: {e}")
        
        return hook
    
    def _create_generic_hook(self, layer_name: str):
        """Create generic hook for unknown layers"""
        def hook(module, input, output):
            try:
                if isinstance(output, torch.Tensor):
                    signal_type = f"generic_activation.{layer_name}"
                    forward_pass_index = self._get_forward_pass_index()
                    signals = {
                        'framework': 'pytorch',
                        'signal_type': signal_type,
                        'layer_name': layer_name,
                        'forward_pass_index': forward_pass_index,  # Distinguishes multiple forward passes during generation
                        'timestamp': time.time(),
                        'request_id': self._get_request_id(),
                        'statistics': self._compute_tensor_statistics(output)
                    }
                    logger.info(
                        "Generic activation layer %s statistics: %s",
                        layer_name,
                        signals["statistics"],
                    )
                    self._export_signal(signals)
            except Exception as e:
                logger.error(f"Error in generic hook: {e}")
        
        return hook

    def _create_embedding_hook(self, embedding_name: str):
        """Capture embedding layer outputs and derived signals."""
        def hook(module, input, output):
            try:
                if isinstance(output, tuple):
                    embedding_output = output[0]
                else:
                    embedding_output = output

                embedding_tensor = self._prepare_tensor(embedding_output)
                if embedding_tensor is None:
                    return

                signal_type = f"embeddings.{embedding_name}"
                forward_pass_index = self._get_forward_pass_index()
                signals = {
                    'framework': 'pytorch',
                    'signal_type': signal_type,
                    'embedding_name': embedding_name,
                    'forward_pass_index': forward_pass_index,  # Distinguishes multiple forward passes during generation
                    'timestamp': time.time(),
                    'request_id': self._get_request_id(),
                    'statistics': self._compute_tensor_statistics(embedding_tensor),
                    'neural_health': self._compute_neural_health(embedding_tensor),
                    'embedding_sample': self._sample_hidden_state(embedding_tensor),
                    'token_statistics': self._compute_token_statistics(embedding_tensor),
                    'feature_statistics': self._compute_feature_statistics(embedding_tensor),
                    'token_norms': self._compute_token_norms(embedding_tensor),
                    'pooled_embedding': self._compute_pooled_embeddings(embedding_tensor),
                    'hidden_state_energy': self._compute_hidden_state_energy(embedding_tensor),
                }

                if self.capture_full_hidden_state:
                    signals['embedding_full'] = embedding_tensor.tolist()

                logger.info(
                    "Embedding layer %s statistics: %s",
                    embedding_name,
                    signals["statistics"],
                )
                logger.info(
                    "Embedding layer %s neural health: %s",
                    embedding_name,
                    signals["neural_health"],
                )
                logger.info(
                    "Embedding layer %s sampled tensor: %s",
                    embedding_name,
                    signals["embedding_sample"],
                )

                self._export_signal(signals)
            except Exception as e:
                logger.error(f"Error in embedding hook: {e}")

        return hook
    
    # Helper methods
    
    def _prepare_tensor(self, tensor: Any) -> Optional[torch.Tensor]:
        """Detach tensor and move to CPU for analysis."""
        if not isinstance(tensor, torch.Tensor):
            return None
        return tensor.detach().to(dtype=torch.float32).cpu()

    def _round_array(self, array: np.ndarray) -> np.ndarray:
        """Round numpy array using configured precision."""
        if self.embedding_precision >= 0:
            return np.round(array, self.embedding_precision)
        return array

    def _sample_hidden_state(self, tensor: torch.Tensor) -> List[Any]:
        """Return a compact numeric snapshot of the hidden state."""
        try:
            if tensor.dim() == 0:
                return []

            if tensor.dim() == 1:
                sample = tensor[:min(self.sample_features, tensor.shape[0])]
            elif tensor.dim() == 2:
                batch_limit = min(self.sample_batch_size, tensor.shape[0])
                feature_limit = min(self.sample_features, tensor.shape[1])
                sample = tensor[:batch_limit, :feature_limit]
            else:
                batch_limit = min(self.sample_batch_size, tensor.shape[0])
                token_limit = min(self.sample_tokens, tensor.shape[1])
                feature_limit = min(self.sample_features, tensor.shape[2])
                sample = tensor[:batch_limit, :token_limit, :feature_limit]

            array = sample.numpy()
            array = self._round_array(array)
            return array.tolist()
        except Exception:
            return []

    def _collect_cls_embeddings(self, hidden_state: torch.Tensor) -> Dict[str, Any]:
        """Collect CLS embeddings and derived metrics."""
        info: Dict[str, Any] = {
            'primary': [],
            'batch': [],
            'norms': [],
            'statistics': {}
        }
        try:
            if hidden_state.dim() < 3 or hidden_state.shape[1] == 0:
                return info

            cls_tokens = hidden_state[:, 0, :]
            if cls_tokens.numel() == 0:
                return info

            primary = cls_tokens[0].numpy()
            info['primary'] = self._round_array(primary).tolist()

            batch_limit = min(self.sample_batch_size, cls_tokens.shape[0])
            batch_sample = cls_tokens[:batch_limit].numpy()
            info['batch'] = self._round_array(batch_sample).tolist()

            norms = cls_tokens.norm(dim=1)
            info['norms'] = norms[:batch_limit].tolist()

            info['statistics'] = {
                'mean': float(cls_tokens.mean().item()),
                'std': float(cls_tokens.std(unbiased=False).item()),
                'norm_mean': float(norms.mean().item()),
                'max': float(cls_tokens.max().item()),
                'min': float(cls_tokens.min().item()),
            }
        except Exception:
            pass
        return info

    def _extract_cls_embedding(self, hidden_state: torch.Tensor) -> List[float]:
        """Maintain backwards compatibility with legacy CLS extraction."""
        cls_info = self._collect_cls_embeddings(hidden_state)
        return cls_info.get('primary', [])

    def _compute_pooled_embeddings(self, hidden_state: torch.Tensor) -> List[Any]:
        """Compute mean pooled embeddings for sampled batch items."""
        try:
            if hidden_state.dim() < 3:
                return []
            pooled = hidden_state.mean(dim=1)
            batch_limit = min(self.sample_batch_size, pooled.shape[0])
            array = pooled[:batch_limit].numpy()
            array = self._round_array(array)
            return array.tolist()
        except Exception:
            return []

    def _compute_tensor_statistics(self, tensor: torch.Tensor) -> Dict[str, float]:
        """Compute comprehensive tensor statistics."""
        tensor_cpu = tensor.detach().cpu().float()
        if tensor_cpu.numel() == 0:
            return {
                'mean': 0.0,
                'std': 0.0,
                'max': 0.0,
                'min': 0.0,
                'shape': list(tensor_cpu.shape)
            }
        return {
            'mean': float(tensor_cpu.mean().item()),
            'std': float(tensor_cpu.std(unbiased=False).item()),
            'max': float(tensor_cpu.max().item()),
            'min': float(tensor_cpu.min().item()),
            'shape': list(tensor_cpu.shape)
        }
    
    def _compute_neural_health(self, tensor: torch.Tensor) -> Dict[str, float]:
        """Compute neural health metrics."""
        tensor_cpu = tensor.detach().cpu().float()
        sparsity = float((tensor_cpu == 0).float().mean().item())
        saturation = float((torch.abs(tensor_cpu) > 0.95).float().mean().item())

        dead_neurons = 0.0
        if tensor_cpu.dim() >= 3:
            dead_neurons = float((tensor_cpu.abs().mean(dim=[0, 1]) < 1e-6).float().mean().item())

        return {
            'sparsity': sparsity,
            'saturation': saturation,
            'dead_neurons': dead_neurons
        }

    def _compute_token_statistics(self, tensor: torch.Tensor) -> List[Dict[str, Any]]:
        """Compute statistics for individual tokens."""
        stats: List[Dict[str, Any]] = []
        try:
            if tensor.dim() < 3:
                return stats

            batch_limit = min(self.sample_batch_size, tensor.shape[0])
            token_limit = min(self.sample_tokens, tensor.shape[1])

            for batch_idx in range(batch_limit):
                for token_idx in range(token_limit):
                    token_vec = tensor[batch_idx, token_idx]
                    stats.append({
                        'batch': batch_idx,
                        'token': token_idx,
                        'mean': float(token_vec.mean().item()),
                        'std': float(token_vec.std(unbiased=False).item()),
                        'norm': float(token_vec.norm().item()),
                        'max': float(token_vec.max().item()),
                        'min': float(token_vec.min().item())
                    })
        except Exception:
            pass
        return stats

    def _compute_feature_statistics(self, tensor: torch.Tensor) -> List[Dict[str, Any]]:
        """Compute statistics across embedding dimensions."""
        stats: List[Dict[str, Any]] = []
        try:
            if tensor.dim() < 3:
                return stats

            batch_limit = min(self.sample_batch_size, tensor.shape[0])
            feature_limit = min(self.sample_features, tensor.shape[2])
            subset = tensor[:batch_limit, :, :feature_limit]

            for feature_idx in range(feature_limit):
                feature_values = subset[:, :, feature_idx]
                stats.append({
                    'feature': feature_idx,
                    'mean': float(feature_values.mean().item()),
                    'std': float(feature_values.std(unbiased=False).item()),
                    'norm': float(feature_values.norm().item()),
                    'max': float(feature_values.max().item()),
                    'min': float(feature_values.min().item())
                })
        except Exception:
            pass
        return stats

    def _compute_token_norms(self, tensor: torch.Tensor) -> List[List[float]]:
        """Return per-token L2 norms for sampled batch items."""
        try:
            if tensor.dim() < 3:
                return []
            norms = tensor.norm(dim=-1)
            batch_limit = min(self.sample_batch_size, norms.shape[0])
            token_limit = min(self.sample_tokens, norms.shape[1])
            subset = norms[:batch_limit, :token_limit]
            return subset.tolist()
        except Exception:
            return []

    def _compute_hidden_state_energy(self, tensor: torch.Tensor) -> float:
        """Compute mean squared activation energy."""
        try:
            return float(tensor.pow(2).mean().item())
        except Exception:
            return 0.0
    
    def _compute_attention_entropy(self, attention: torch.Tensor) -> List[float]:
        """Compute entropy per attention head"""
        entropies = []
        try:
            for head in range(attention.shape[1]):
                head_attn = attention[0, head, :, :]
                entropy = -(head_attn * torch.log(head_attn + 1e-9)).sum(dim=-1).mean()
                entropies.append(float(entropy))
        except:
            pass
        return entropies
    
    def _compute_stability(self, tensor: torch.Tensor) -> float:
        """Compute neural stability score"""
        variance = float(tensor.var())
        return 1.0 / (1.0 + variance)
    
    def _quick_ood_estimate(self, embedding: torch.Tensor) -> float:
        """Quick out-of-domain estimation"""
        sparsity = float((embedding == 0).float().mean())
        norm = float(torch.norm(embedding))
        
        # Simple heuristic: high sparsity + low norm suggests OOD
        if sparsity > 0.3 and norm < 15.0:
            return -1.0  # Likely out-of-domain
        else:
            return 1.0   # Likely in-domain
    
    # ------------------------------------------------------------------ #
    # Request/response capture helpers
    # ------------------------------------------------------------------ #

    def _export_request_payload(
        self,
        request_id: str,
        payload: Dict[str, Any],
        metadata_override: Optional[Dict[str, Any]] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ):
        if not self.capture_request_payload:
            return
        metadata = self._build_request_metadata(
            success=None,
            metadata_override=metadata_override,
            extra_metadata=extra_metadata,
        )
        exporter = getattr(self, "exporter", None)
        if hasattr(exporter, "export_request_payload"):
            try:
                exporter.export_request_payload(request_id, payload, metadata=metadata)
            except Exception as exc:
                logger.error("Failed to export request payload: %s", exc)

    def _export_request_response(
        self,
        request_id: str,
        response_payload: Dict[str, Any],
        success: Optional[bool],
        metadata_override: Optional[Dict[str, Any]] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ):
        if not self.capture_response_payload:
            return
        metadata = self._build_request_metadata(
            success=success,
            metadata_override=metadata_override,
            extra_metadata=extra_metadata,
        )
        exporter = getattr(self, "exporter", None)
        if hasattr(exporter, "export_request_response"):
            try:
                exporter.export_request_response(request_id, response_payload, metadata=metadata)
            except Exception as exc:
                logger.error("Failed to export request response: %s", exc)

    def _build_request_metadata(
        self,
        success: Optional[bool],
        metadata_override: Optional[Dict[str, Any]] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Build minimal request metadata.
        Most information is already in signal payloads, so metadata should be lightweight
        and only contain request-specific information not available in signals.
        """
        metadata: Dict[str, Any] = {}
        
        # Add user-defined metadata from config (intentional custom fields)
        if self.request_metadata:
            metadata.update(self.request_metadata)
        
        # Add user-provided metadata override (intentional custom fields)
        if metadata_override:
            metadata.update(metadata_override)
        
        # Add extra metadata (typically contains 'variant' to distinguish request types)
        if extra_metadata:
            # Only keep essential fields like 'variant', filter out signal-related fields
            variant = extra_metadata.get("variant")
            if variant:
                metadata["variant"] = variant
        
        # Add success status for response metadata (not available in signals)
        if success is not None:
            metadata["success"] = success
        
        # Remove fields that are already in signal payloads to avoid duplication
        # Signals already include: framework, timestamp, request_id, statistics, 
        # neural_health, embedding fields, layer info, etc.
        signal_fields_to_remove = {
            # Framework info (already in every signal)
            "framework",
            # Time and request tracking (already in signals and request body)
            "timestamp",
            "request_id",
            # Embedding fields (already in signals)
            "embedding", "embedding_vector", "cls_embedding", "pooled_embedding",
            # Signal analysis fields (already in signals)
            "statistics", "neural_health", "attention_metrics", "domain_indicators",
            # Layer/network info (already in signals)
            "layer_type", "layer_index", "layer_name", "signal_type",
        }
        for field in signal_fields_to_remove:
            metadata.pop(field, None)
        
        return metadata

    def _serialize_call_arguments(self, args: Iterable[Any], kwargs: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            "args": self._serialize_sequence(args, depth=0),
            "kwargs": self._serialize_mapping(kwargs, depth=0),
        }

    def _serialize_sequence(self, seq: Iterable[Any], depth: int) -> List[Any]:
        result: List[Any] = []
        total_len = len(seq) if hasattr(seq, "__len__") else None  # type: ignore[arg-type]
        for idx, item in enumerate(seq):
            if idx >= self.payload_max_items:
                remaining = None
                if total_len is not None:
                    remaining = max(total_len - self.payload_max_items, 0)
                result.append({"__truncated__": True, "remaining": remaining})
                break
            result.append(self._serialize_value(item, depth + 1))
        return result

    def _serialize_mapping(self, mapping: Mapping[str, Any], depth: int) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        try:
            total_len = len(mapping)  # type: ignore[arg-type]
        except TypeError:
            total_len = None
        for idx, (key, value) in enumerate(mapping.items()):
            if idx >= self.payload_max_items:
                result["__truncated__"] = True
                if total_len is not None:
                    result["__remaining__"] = max(total_len - self.payload_max_items, 0)
                break
            result[str(key)] = self._serialize_value(value, depth + 1)
        return result

    def _serialize_value(self, value: Any, depth: int = 0) -> Any:
        if depth > self.payload_max_depth:
            return "<max-depth>"

        try:
            if isinstance(value, torch.Tensor):
                return self._tensor_summary_for_payload(value)
            if isinstance(value, (list, tuple)):
                return self._serialize_sequence(value, depth + 1)
            if isinstance(value, dict):
                return self._serialize_mapping(value, depth + 1)
            if hasattr(value, "_asdict"):
                return self._serialize_mapping(value._asdict(), depth + 1)  # type: ignore[attr-defined]
            if hasattr(value, "to_tuple"):
                return self._serialize_sequence(value.to_tuple(), depth + 1)  # type: ignore[attr-defined]
            if hasattr(value, "__dict__") and value.__dict__:
                return self._serialize_mapping(value.__dict__, depth + 1)
            if isinstance(value, (str, int, float, bool)) or value is None:
                return value
            if isinstance(value, np.ndarray):
                return {
                    "type": "ndarray",
                    "shape": list(value.shape),
                    "sample": self._sample_numpy_array(value),
                }
        except Exception:
            pass

        return repr(value)

    def _tensor_summary_for_payload(self, tensor: torch.Tensor) -> Dict[str, Any]:
        tensor_cpu = tensor.detach().cpu()
        summary: Dict[str, Any] = {
            "type": "tensor",
            "shape": list(tensor_cpu.shape),
            "dtype": str(tensor_cpu.dtype),
            "device": str(tensor.device),
        }
        summary["sample"] = self._tensor_sample_for_payload(tensor_cpu)
        summary["statistics"] = self._compute_tensor_statistics(tensor)
        return summary

    def _tensor_sample_for_payload(self, tensor: torch.Tensor) -> List[Any]:
        try:
            flat = tensor.flatten()
            max_elements = self.payload_tensor_elements
            if flat.numel() <= max_elements:
                return flat.tolist()
            return flat[:max_elements].tolist()
        except Exception:
            return []

    def _extract_logits_tensor(self, result: Any) -> Optional[torch.Tensor]:
        """
        Extract logits tensor from model forward output.
        Handles HuggingFace-style outputs (e.g. .logits) and tuple/dict.
        """
        if result is None:
            return None
        if isinstance(result, torch.Tensor):
            return result
        if hasattr(result, "logits"):
            logits = getattr(result, "logits", None)
            if isinstance(logits, torch.Tensor):
                return logits
        if isinstance(result, (list, tuple)) and len(result) > 0:
            first = result[0]
            if isinstance(first, torch.Tensor):
                return first
        if isinstance(result, dict) and "logits" in result:
            logits = result["logits"]
            if isinstance(logits, torch.Tensor):
                return logits
        return None

    def _serialize_logits_or_probs_tensor(self, tensor: torch.Tensor) -> Dict[str, Any]:
        """
        Serialize logits or probabilities tensor for response payload.
        Returns shape and a sample of values (bounded by logits_sample_size).
        """
        try:
            t = tensor.detach().cpu()
            shape = list(t.shape)
            flat = t.flatten()
            n = min(flat.numel(), self.logits_sample_size)
            sample = flat[:n].tolist()
            return {
                "shape": shape,
                "sample": sample,
                "numel": flat.numel(),
            }
        except Exception:
            return {"shape": [], "sample": [], "numel": 0}

    def _serialize_output_for_response(
        self, result: Any, exclude_logits_from_output: bool
    ) -> Any:
        """
        Serialize model output for the 'output' field of the response payload.
        When exclude_logits_from_output is True, strips logits from the serialized
        output (so logits are only sent via the dedicated logits/probabilities fields).
        """
        if not exclude_logits_from_output:
            return self._serialize_value(result)
        try:
            if hasattr(result, "_asdict"):
                d = dict(result._asdict())
                d.pop("logits", None)
                return self._serialize_value(d)
            if hasattr(result, "__dict__") and result.__dict__:
                d = dict(result.__dict__)
                d.pop("logits", None)
                return self._serialize_value(d)
            if isinstance(result, dict):
                d = dict(result)
                d.pop("logits", None)
                return self._serialize_value(d)
        except Exception:
            pass
        return self._serialize_value(result)

    def _sample_numpy_array(self, array: np.ndarray) -> List[Any]:
        try:
            flat = array.flatten()
            if flat.size <= self.payload_tensor_elements:
                return flat.tolist()
            return flat[: self.payload_tensor_elements].tolist()
        except Exception:
            return []
    
    def _wrap_model_forward(self, model):
        """Wrap the model forward pass to assign request-scoped IDs."""
        if hasattr(model, "_onex_original_forward"):
            return
        
        original_forward = model.forward
        setattr(model, "_onex_original_forward", original_forward)
        adapter = self

        @wraps(original_forward)
        def wrapped_forward(*args, **kwargs):
            request_id = adapter._get_request_id()
            metadata_override = getattr(adapter._request_local, "metadata_override", None)
            raw_payload = getattr(adapter._request_local, "raw_payload", None)
            context_active = bool(getattr(adapter._request_local, "context_active", False))

            generated_request_id = False
            if request_id is None:
                request_id = uuid.uuid4().hex
                adapter._set_request_id(request_id)
                generated_request_id = True
                metadata_override = getattr(adapter._request_local, "metadata_override", None)
                raw_payload = getattr(adapter._request_local, "raw_payload", None)
            
            # Track forward pass index for this request (increments on each forward call)
            # This helps distinguish signals from multiple forward passes during generation
            forward_pass_index = getattr(adapter._request_local, "forward_pass_index", 0)
            adapter._request_local.forward_pass_index = forward_pass_index + 1

            # Only export request payload once per request_id
            # This prevents duplicate payloads when forward() is called multiple times
            # (e.g., during GPT text generation where forward is called per token)
            with adapter._exported_request_payloads_lock:
                if request_id not in adapter._exported_request_payloads:
                    model_inputs = adapter._serialize_call_arguments(args, kwargs)
                    payload_event: Dict[str, Any] = {"model_inputs": model_inputs}
                    if raw_payload is not None:
                        payload_event["raw"] = raw_payload

                    adapter._export_request_payload(
                        request_id,
                        payload_event,
                        metadata_override=metadata_override,
                        extra_metadata={"variant": "model_inputs"},
                    )
                    adapter._exported_request_payloads.add(request_id)
            try:
                result = original_forward(*args, **kwargs)
            except Exception as exc:
                # Only export error response once per request_id
                with adapter._exported_request_responses_lock:
                    if request_id not in adapter._exported_request_responses:
                        adapter._export_request_response(
                            request_id,
                            {"error": repr(exc)},
                            success=False,
                            metadata_override=metadata_override,
                            extra_metadata={"variant": "model_output"},
                        )
                        adapter._exported_request_responses.add(request_id)
                raise
            else:
                # Only export success response once per request_id
                with adapter._exported_request_responses_lock:
                    if request_id not in adapter._exported_request_responses:
                        response_payload: Dict[str, Any] = {}
                        capture_any = adapter.capture_logits or adapter.capture_probabilities
                        logits_tensor = (
                            adapter._extract_logits_tensor(result) if capture_any else None
                        )

                        response_payload["output"] = adapter._serialize_output_for_response(
                            result, exclude_logits_from_output=capture_any
                        )
                        if logits_tensor is not None:
                            if adapter.capture_logits:
                                response_payload["logits"] = (
                                    adapter._serialize_logits_or_probs_tensor(logits_tensor)
                                )
                            if adapter.capture_probabilities:
                                try:
                                    probs = torch.softmax(
                                        logits_tensor.float(), dim=-1
                                    )
                                    response_payload["probabilities"] = (
                                        adapter._serialize_logits_or_probs_tensor(probs)
                                    )
                                except Exception:
                                    pass

                        adapter._export_request_response(
                            request_id,
                            response_payload,
                            success=True,
                            metadata_override=metadata_override,
                            extra_metadata={"variant": "model_output"},
                        )
                        adapter._exported_request_responses.add(request_id)
                return result
            finally:
                if generated_request_id or not context_active:
                    adapter._clear_request_context()
                    # Remove from exported payloads and responses sets when request context is cleared
                    with adapter._exported_request_payloads_lock:
                        adapter._exported_request_payloads.discard(request_id)
                    with adapter._exported_request_responses_lock:
                        adapter._exported_request_responses.discard(request_id)

        model.forward = wrapped_forward

    def start_request_context(
        self,
        payload: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> str:
        request_id = request_id or uuid.uuid4().hex
        self._set_request_id(request_id)
        self._request_local.raw_payload = payload
        self._request_local.metadata_override = metadata or {}
        self._request_local.context_active = True
        self._request_local.forward_pass_index = 0  # Reset forward pass counter for new request
        return request_id

    def end_request_context(self):
        request_id = self._get_request_id()
        self._clear_request_context()
        # Remove from exported payloads and responses sets when request context ends
        if request_id:
            with self._exported_request_payloads_lock:
                self._exported_request_payloads.discard(request_id)
            with self._exported_request_responses_lock:
                self._exported_request_responses.discard(request_id)
        # Flush signals immediately when request context ends
        self.exporter.flush()

    def export_manual_response(
        self,
        request_id: str,
        response_payload: Dict[str, Any],
        success: Optional[bool] = None,
        metadata_override: Optional[Dict[str, Any]] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ):
        self._export_request_response(
            request_id,
            response_payload,
            success=success,
            metadata_override=metadata_override,
            extra_metadata=extra_metadata,
        )

    def _set_request_id(self, request_id: str):
        self._request_local.request_id = request_id

    def _get_request_id(self) -> Optional[str]:
        return getattr(self._request_local, "request_id", None)
    
    def _get_forward_pass_index(self) -> int:
        """Get the current forward pass index for the active request"""
        return getattr(self._request_local, "forward_pass_index", 0)

    def _clear_request_context(self):
        for attr in ("request_id", "raw_payload", "metadata_override", "context_active", "forward_pass_index"):
            if hasattr(self._request_local, attr):
                delattr(self._request_local, attr)
    
    def cleanup(self):
        """Remove all hooks"""
        self._clear_request_context()
        for hook in self.hooks:
            hook.remove()
        self.hooks.clear()
        logger.info("Cleaned up all PyTorch hooks")
