"""
Matryoshka ColBERT: Multi-dimensional ColBERT embeddings with PyLate.

Usage:
    from colbert_matryoshka import MatryoshkaColBERT

    # Load model
    model = MatryoshkaColBERT.from_pretrained("dragonkue/colbert-ko-0.1b")

    # Set embedding dimension (32, 64, 96, or 128)
    model.set_active_dim(128)

    # Encode
    query_embeddings = model.encode(["query"], is_query=True)
    doc_embeddings = model.encode(["document"], is_query=False)
"""

from colbert_matryoshka.model import (
    MatryoshkaColBERT,
    MatryoshkaColBERTWrapper,  # Backward compatibility alias
    create_skiplist_mask,
    get_punctuation_skiplist,
)

__version__ = "0.1.1"
__all__ = [
    "MatryoshkaColBERT",
    "MatryoshkaColBERTWrapper",
    "create_skiplist_mask",
    "get_punctuation_skiplist",
]
