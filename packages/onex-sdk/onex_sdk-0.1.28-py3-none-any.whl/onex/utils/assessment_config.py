"""
Assessment Configuration
Defines which signal fields are required for each assessment type.
"""

from typing import Dict, List, Set

# Assessment to required fields mapping
ASSESSMENT_FIELD_MATRIX: Dict[str, Set[str]] = {
    "OOD": {
        "signal_type",      # Required: signal type identifier
        "embedding",        # Required: embedding vector for OOD detection
        "embedding_vector", # Alternative field name for embedding
        "neural_health",
        "attention_metrics",
        "domain_indicators"
    },
    # Future assessments can be added here:
    # "DRIFT": {"signal_type", "statistics", "neural_health"},
    # "ANOMALY": {"signal_type", "statistics", "attention_metrics"},
}

# Common fields that should always be included if present
COMMON_FIELDS: Set[str] = {
    "framework",
    "timestamp",
    "request_id",
    "signal_type",
    "forward_pass_index",  # Distinguishes multiple forward passes during generation
}


def get_required_fields(assessments: List[str]) -> Set[str]:
    """
    Get all required fields for the given assessments.
    
    Args:
        assessments: List of assessment names (e.g., ["OOD"])
    
    Returns:
        Set of required field names
    """
    required_fields: Set[str] = set(COMMON_FIELDS)
    
    for assessment in assessments:
        assessment_upper = assessment.upper()
        if assessment_upper in ASSESSMENT_FIELD_MATRIX:
            required_fields.update(ASSESSMENT_FIELD_MATRIX[assessment_upper])
    
    return required_fields


def filter_signal_by_assessments(
    signal: Dict,
    enabled_assessments: List[str]
) -> Dict:
    """
    Filter signal fields based on enabled assessments.
    Only includes fields required by the enabled assessments.
    
    Args:
        signal: Full signal dictionary
        enabled_assessments: List of enabled assessment names
    
    Returns:
        Filtered signal dictionary with only required fields
    """
    if not enabled_assessments:
        # If no assessments enabled, return full signal (backward compatibility)
        return signal
    
    required_fields = get_required_fields(enabled_assessments)
    filtered_signal = {}
    
    # Always include common fields and required assessment fields
    for field in required_fields:
        if field in signal:
            filtered_signal[field] = signal[field]
    
    # Handle embedding field mapping for OOD assessment
    # OOD requires 'embedding_vector', but signals may have various embedding field names
    if "OOD" in [a.upper() for a in enabled_assessments]:
        # Check various embedding field names and normalize to 'embedding_vector'
        embedding_value = None
        
        # Priority 1: Direct embedding or embedding_vector fields
        if "embedding" in signal:
            embedding_value = signal["embedding"]
        elif "embedding_vector" in signal:
            embedding_value = signal["embedding_vector"]
        # Priority 2: cls_embedding (for pre-classification signals)
        elif "cls_embedding" in signal:
            # For OOD, use primary CLS embedding (first element if it's a list)
            cls_emb = signal.get("cls_embedding", [])
            if isinstance(cls_emb, list) and len(cls_emb) > 0:
                embedding_value = cls_emb[0] if isinstance(cls_emb[0], list) else cls_emb
        # Priority 3: pooled_embedding (for embeddings.bert_embeddings signals)
        elif "pooled_embedding" in signal:
            pooled_emb = signal.get("pooled_embedding", [])
            if isinstance(pooled_emb, list) and len(pooled_emb) > 0:
                # Use first item from batch if it's a list of embeddings
                embedding_value = pooled_emb[0] if isinstance(pooled_emb[0], list) else pooled_emb
        
        if embedding_value is not None:
            filtered_signal["embedding_vector"] = embedding_value
    
    # Handle embedding_vector as an alias for embedding (non-OOD cases)
    if "embedding_vector" in required_fields and "embedding" in signal and "embedding_vector" not in filtered_signal:
        filtered_signal["embedding_vector"] = signal["embedding"]
    
    # Also handle the reverse: if embedding is required but signal has embedding_vector
    if "embedding" in required_fields and "embedding_vector" in signal and "embedding" not in filtered_signal:
        filtered_signal["embedding"] = signal["embedding_vector"]
    
    # Ensure signal_type is always present (required for all assessments)
    if "signal_type" not in filtered_signal and "signal_type" in signal:
        filtered_signal["signal_type"] = signal["signal_type"]
    
    return filtered_signal


def get_available_assessments() -> List[str]:
    """Get list of all available assessment types."""
    return list(ASSESSMENT_FIELD_MATRIX.keys())

