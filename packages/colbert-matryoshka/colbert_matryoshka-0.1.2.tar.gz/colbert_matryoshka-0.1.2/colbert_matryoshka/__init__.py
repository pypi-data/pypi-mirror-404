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

__version__ = "0.1.2"


def __getattr__(name):
    """Lazy import to avoid immediate pylate dependency check."""
    if name in ("MatryoshkaColBERT", "MatryoshkaColBERTWrapper",
                "create_skiplist_mask", "get_punctuation_skiplist", "load_pretrained"):
        from colbert_matryoshka.model import (
            MatryoshkaColBERT,
            MatryoshkaColBERTWrapper,
            create_skiplist_mask,
            get_punctuation_skiplist,
            load_pretrained,
        )
        globals().update({
            "MatryoshkaColBERT": MatryoshkaColBERT,
            "MatryoshkaColBERTWrapper": MatryoshkaColBERTWrapper,
            "create_skiplist_mask": create_skiplist_mask,
            "get_punctuation_skiplist": get_punctuation_skiplist,
            "load_pretrained": load_pretrained,
        })
        return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "MatryoshkaColBERT",
    "MatryoshkaColBERTWrapper",
    "create_skiplist_mask",
    "get_punctuation_skiplist",
    "load_pretrained",
]
