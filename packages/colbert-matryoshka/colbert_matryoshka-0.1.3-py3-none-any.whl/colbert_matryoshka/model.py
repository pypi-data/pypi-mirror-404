"""
Matryoshka ColBERT Model for multi-dimensional inference.

This module provides the MatryoshkaColBERT class that inherits from PyLate's ColBERT
and adds Multiple Linear Heads for Matryoshka embeddings (Jina-ColBERT-v2 style).

Usage:
    from colbert_matryoshka import MatryoshkaColBERT

    # Load model with matryoshka heads
    model = MatryoshkaColBERT.from_pretrained("dragonkue/colbert-ko-0.1b")

    # Set active dimension (32, 64, 96, or 128)
    model.set_active_dim(64)

    # Encode texts
    query_embeddings = model.encode(["query text"], is_query=True)
    doc_embeddings = model.encode(["document text"], is_query=False)
"""

import logging
import os
import string
from typing import List, Optional, Dict, Union

import torch
import torch.nn as nn
import torch.nn.functional as F

logger = logging.getLogger(__name__)


def create_skiplist_mask(
    input_ids: torch.Tensor,
    skiplist: List[int],
) -> torch.Tensor:
    """
    Create a mask that filters out skiplist tokens (e.g., punctuation).

    Args:
        input_ids: Token IDs [batch, seq_len]
        skiplist: List of token IDs to skip

    Returns:
        mask: Boolean mask [batch, seq_len] where True = keep, False = skip
    """
    if not skiplist:
        return torch.ones_like(input_ids, dtype=torch.bool)

    mask = torch.ones_like(input_ids, dtype=torch.bool)
    for token_id in skiplist:
        mask = mask & (input_ids != token_id)

    return mask


def get_punctuation_skiplist(tokenizer) -> List[int]:
    """
    Get token IDs for punctuation characters.

    Args:
        tokenizer: HuggingFace tokenizer

    Returns:
        List of token IDs corresponding to punctuation characters
    """
    skiplist = []
    for char in string.punctuation:
        token_id = tokenizer.convert_tokens_to_ids(char)
        if token_id != tokenizer.unk_token_id:
            skiplist.append(token_id)
    return skiplist


# Import PyLate ColBERT
PYLATE_IMPORT_ERROR = None
try:
    from pylate.models import ColBERT as PyLateColBERT
    PYLATE_AVAILABLE = True
except Exception as e:
    PyLateColBERT = nn.Module
    PYLATE_AVAILABLE = False
    PYLATE_IMPORT_ERROR = e
    logger.warning(f"PyLate not available: {e}. Install with: pip install pylate")


class MatryoshkaColBERT(PyLateColBERT):
    """
    ColBERT model with Multiple Linear Heads for Matryoshka inference.

    Inherits from PyLate's ColBERT and adds multiple projection heads for
    different embedding dimensions, following Jina-ColBERT-v2 approach.

    Architecture:
        [Encoder] -> hidden_states (768)
                  -> [Linear Head 128] -> 128-dim output
                  -> [Linear Head 96]  -> 96-dim output
                  -> [Linear Head 64]  -> 64-dim output
                  -> [Linear Head 32]  -> 32-dim output

    Args:
        model_name_or_path: Path to pretrained model or model identifier
        matryoshka_dims: List of output dimensions for each head
        **kwargs: Additional arguments passed to PyLate ColBERT
    """

    def __init__(
        self,
        model_name_or_path: str,
        matryoshka_dims: Optional[List[int]] = None,
        **kwargs,
    ):
        if not PYLATE_AVAILABLE:
            error_msg = f"PyLate import failed: {PYLATE_IMPORT_ERROR}" if PYLATE_IMPORT_ERROR else "PyLate is required"
            raise ImportError(f"{error_msg}. Install with: pip install pylate")

        if matryoshka_dims is None:
            matryoshka_dims = [32, 64, 96, 128]

        # Filter out transformers-specific arguments that PyLate doesn't accept
        transformers_args = ['config', 'cache_dir', 'force_download', 'proxies',
                            'resume_download', 'local_files_only', 'token',
                            'revision', 'use_safetensors', 'torch_dtype',
                            'attn_implementation', 'device_map']
        for arg in transformers_args:
            kwargs.pop(arg, None)

        # Initialize parent PyLate ColBERT
        super().__init__(model_name_or_path=model_name_or_path, **kwargs)

        self.matryoshka_dims = sorted(matryoshka_dims)
        self.max_dim = max(matryoshka_dims)

        # Get hidden size from encoder
        self._hidden_size = self._get_hidden_size()
        logger.info(f"Detected hidden size: {self._hidden_size}")

        # Check if model uses ModernBert
        self._is_modern_bert = self._check_modern_bert()
        if self._is_modern_bert:
            logger.info("Detected ModernBert - will remove token_type_ids from inputs")
            self._patch_for_modern_bert()

        # Create multiple projection heads
        self.projection_heads = nn.ModuleDict()
        for dim in self.matryoshka_dims:
            self.projection_heads[str(dim)] = nn.Linear(
                self._hidden_size, dim, bias=False
            )
            logger.info(f"Created projection head: {self._hidden_size} -> {dim}")

        # Initialize projection heads (copy weights from Dense if matching)
        self._init_projection_heads()

        # Current active dimension (for inference)
        self.active_dim = self.max_dim

        logger.info(f"MatryoshkaColBERT initialized with dims: {self.matryoshka_dims}")

    def _get_hidden_size(self) -> int:
        """Get the hidden size of the encoder."""
        try:
            return self[0].get_word_embedding_dimension()
        except Exception:
            pass

        for module in self.children():
            if hasattr(module, 'auto_model'):
                return module.auto_model.config.hidden_size

        return 768

    def _check_modern_bert(self) -> bool:
        """Check if the underlying model uses ModernBert architecture."""
        try:
            model_type = getattr(self[0].auto_model.config, 'model_type', '')
            if 'modernbert' in model_type.lower():
                return True
            class_name = self[0].auto_model.__class__.__name__
            if 'ModernBert' in class_name:
                return True
        except Exception:
            pass
        return False

    def _patch_for_modern_bert(self):
        """Patch the transformer to remove token_type_ids for ModernBert."""
        try:
            transformer = self[0]
            original_forward = transformer.forward

            def patched_forward(features, *args, _orig_fn=original_forward, **kwargs):
                if isinstance(features, dict) and 'token_type_ids' in features:
                    features = {k: v for k, v in features.items() if k != 'token_type_ids'}
                return _orig_fn(features, *args, **kwargs)

            transformer.forward = patched_forward
            logger.info("Patched Transformer module for ModernBert compatibility")
        except Exception as e:
            logger.warning(f"Could not patch for ModernBert: {e}")

    def _init_projection_heads(self):
        """
        Initialize projection heads.

        Copy PyLate's Dense layer weights to the matching projection head.
        Other heads use Xavier initialization.
        """
        pylate_dense = None
        pylate_out_features = None

        try:
            if len(self) >= 2:
                dense_module = self[1]
                if hasattr(dense_module, 'linear'):
                    pylate_dense = dense_module.linear
                    pylate_out_features = pylate_dense.out_features
                    logger.info(f"Found PyLate Dense layer: {pylate_dense.in_features} -> {pylate_out_features}")
        except Exception as e:
            logger.warning(f"Could not access PyLate Dense layer: {e}")

        for dim_str, head in self.projection_heads.items():
            dim = int(dim_str)

            if pylate_dense is not None and dim == pylate_out_features:
                with torch.no_grad():
                    head.weight.copy_(pylate_dense.weight)
                logger.info(f"Copied PyLate Dense weights to projection head {dim}")
            else:
                nn.init.xavier_uniform_(head.weight)
                logger.info(f"Xavier init for projection head {dim}")

    def get_sentence_embedding_dimension(self) -> int:
        """Return the active dimension for sentence embeddings."""
        return self.active_dim

    def set_active_dim(self, dim: int):
        """Set the active dimension for inference."""
        if str(dim) not in self.projection_heads:
            available = list(self.projection_heads.keys())
            raise ValueError(f"Dimension {dim} not available. Available: {available}")
        self.active_dim = dim

    def _get_transformer_output(
        self,
        features: Dict[str, torch.Tensor]
    ) -> torch.Tensor:
        """
        Get the raw transformer output before projection.

        Returns: [batch, seq_len, hidden_size]
        """
        transformer = self[0]

        if self._is_modern_bert and 'token_type_ids' in features:
            features = {k: v for k, v in features.items() if k != 'token_type_ids'}

        trans_features = transformer(features)

        if isinstance(trans_features, dict):
            token_embeddings = trans_features.get(
                'token_embeddings',
                trans_features.get('last_hidden_state')
            )
        else:
            token_embeddings = trans_features

        return token_embeddings

    def forward(
        self,
        input: Dict[str, torch.Tensor],
        target_dim: Optional[int] = None,
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass with specified dimension.

        Args:
            input: Tokenized input features
            target_dim: Target embedding dimension (uses active_dim if None)

        Returns:
            Dict with 'token_embeddings', 'input_ids', 'attention_mask' keys
        """
        dim = target_dim or self.active_dim

        token_embeddings = self._get_transformer_output(input)

        if str(dim) in self.projection_heads:
            projected = self.projection_heads[str(dim)](token_embeddings)
        else:
            available_dims = [int(d) for d in self.projection_heads.keys()]
            closest_dim = min(available_dims, key=lambda x: abs(x - dim))
            projected = self.projection_heads[str(closest_dim)](token_embeddings)
            logger.warning(f"Requested dim {dim} not available, using {closest_dim}")

        return {
            'token_embeddings': projected,
            'input_ids': input.get('input_ids'),
            'attention_mask': input.get('attention_mask'),
        }

    def encode(
        self,
        sentences: Union[str, List[str]],
        is_query: bool = True,
        batch_size: int = 32,
        convert_to_numpy: bool = True,
        show_progress_bar: bool = None,
        normalize_embeddings: bool = True,
        **kwargs,
    ):
        """
        Encode texts using the active projection head.

        Args:
            sentences: Text(s) to encode
            is_query: Whether these are queries
            batch_size: Batch size for encoding
            convert_to_numpy: Whether to convert output to numpy
            show_progress_bar: Whether to show progress bar
            normalize_embeddings: Whether to L2-normalize embeddings

        Returns:
            List of embeddings, each of shape [num_valid_tokens, active_dim]
        """
        from tqdm import tqdm
        from sentence_transformers.util import batch_to_device

        self.eval()
        device = self.device

        # Handle single string input
        input_was_string = False
        if isinstance(sentences, str):
            sentences = [sentences]
            input_was_string = True

        all_embeddings = []
        iterator = range(0, len(sentences), batch_size)
        if show_progress_bar:
            desc = "Encoding queries" if is_query else "Encoding documents"
            iterator = tqdm(iterator, desc=desc)

        with torch.no_grad():
            for start_idx in iterator:
                batch_texts = sentences[start_idx:start_idx + batch_size]

                features = self.tokenize(batch_texts, is_query=is_query)
                features = batch_to_device(features, device)

                output = self.forward(features, target_dim=self.active_dim)
                embeddings = output['token_embeddings']

                input_ids = features.get('input_ids')
                attention_mask = features.get('attention_mask')

                for i in range(embeddings.size(0)):
                    emb = embeddings[i]

                    if not is_query:
                        if input_ids is not None and self.skiplist:
                            skiplist_mask = create_skiplist_mask(
                                input_ids[i:i+1], self.skiplist
                            ).squeeze(0)
                            if attention_mask is not None:
                                mask = torch.logical_and(skiplist_mask, attention_mask[i].bool())
                            else:
                                mask = skiplist_mask
                        elif attention_mask is not None:
                            mask = attention_mask[i].bool()
                        else:
                            mask = torch.ones(emb.size(0), dtype=torch.bool, device=device)
                    else:
                        if self.do_query_expansion:
                            mask = torch.ones(emb.size(0), dtype=torch.bool, device=device)
                        elif attention_mask is not None:
                            mask = attention_mask[i].bool()
                        else:
                            mask = torch.ones(emb.size(0), dtype=torch.bool, device=device)

                    emb = emb[mask]

                    if normalize_embeddings:
                        emb = F.normalize(emb, p=2, dim=-1)

                    if convert_to_numpy:
                        emb = emb.cpu().numpy()

                    all_embeddings.append(emb)

        if input_was_string:
            return all_embeddings[0]
        return all_embeddings

    def save_pretrained(self, path: str, **kwargs):
        """Save the model and projection heads."""
        super().save_pretrained(path, **kwargs)

        heads_path = os.path.join(path, 'matryoshka_heads.pt')
        torch.save({
            'matryoshka_dims': self.matryoshka_dims,
            'projection_heads': self.projection_heads.state_dict(),
            'hidden_size': self._hidden_size,
            'active_dim': self.active_dim,
        }, heads_path)
        logger.info(f"Saved Matryoshka heads to {heads_path}")

    @classmethod
    def from_pretrained(cls, path: str, trust_remote_code: bool = True, **kwargs):
        """
        Load a MatryoshkaColBERT model from a saved checkpoint.

        Args:
            path: Path to the model or HuggingFace model ID
            trust_remote_code: Whether to trust remote code
            **kwargs: Additional arguments

        Returns:
            MatryoshkaColBERT with loaded projection heads
        """
        # Filter out transformers-specific arguments that PyLate doesn't accept
        transformers_args = ['config', 'cache_dir', 'force_download', 'proxies',
                            'resume_download', 'local_files_only', 'token',
                            'revision', 'use_safetensors', 'torch_dtype',
                            'attn_implementation', 'device_map']
        for arg in transformers_args:
            kwargs.pop(arg, None)

        # Try to find heads file
        if os.path.isdir(path):
            heads_path = os.path.join(path, 'matryoshka_heads.pt')
        else:
            from huggingface_hub import hf_hub_download
            try:
                heads_path = hf_hub_download(repo_id=path, filename='matryoshka_heads.pt')
            except Exception as e:
                logger.warning(f"Could not download matryoshka_heads.pt: {e}")
                heads_path = None

        if heads_path and os.path.exists(heads_path):
            checkpoint = torch.load(heads_path, map_location='cpu', weights_only=False)
            matryoshka_dims = checkpoint.get('matryoshka_dims', checkpoint.get('dims', [32, 64, 96, 128]))

            # Create model with matryoshka dims
            model = cls(
                model_name_or_path=path,
                matryoshka_dims=matryoshka_dims,
                trust_remote_code=trust_remote_code,
                **kwargs
            )

            # Load projection head weights
            model.projection_heads.load_state_dict(checkpoint['projection_heads'])
            model.active_dim = checkpoint.get('active_dim', max(matryoshka_dims))

            # Move projection heads to model device
            model.projection_heads = model.projection_heads.to(model.device)

            logger.info(f"Loaded Matryoshka heads from {heads_path}")
            return model
        else:
            logger.warning(f"No Matryoshka heads found at {heads_path}, loading as regular ColBERT")
            from pylate.models import ColBERT
            return ColBERT(path, trust_remote_code=trust_remote_code, **kwargs)

    @classmethod
    def from_colbert(
        cls,
        model: "PyLateColBERT",
        dims: Optional[List[int]] = None,
        do_query_expansion: Optional[bool] = None,
    ) -> "MatryoshkaColBERT":
        """
        Create a MatryoshkaColBERT by wrapping an existing PyLate ColBERT model.

        Args:
            model: Existing PyLate ColBERT model
            dims: List of output dimensions for projection heads
            do_query_expansion: Override do_query_expansion setting

        Returns:
            MatryoshkaColBERT instance with the same weights as the input model
        """
        if not PYLATE_AVAILABLE:
            error_msg = f"PyLate import failed: {PYLATE_IMPORT_ERROR}" if PYLATE_IMPORT_ERROR else "PyLate is required"
            raise ImportError(f"{error_msg}. Install with: pip install pylate")

        if dims is None:
            dims = [32, 64, 96, 128]

        instance = cls.__new__(cls)
        nn.Module.__init__(instance)

        # Copy the internal _modules dict
        instance._modules = model._modules.copy()

        # Copy PyLate ColBERT attributes
        instance.query_prefix = model.query_prefix
        instance.document_prefix = model.document_prefix
        instance.query_length = model.query_length
        instance.document_length = model.document_length
        instance.do_query_expansion = do_query_expansion if do_query_expansion is not None else model.do_query_expansion
        instance.attend_to_expansion_tokens = model.attend_to_expansion_tokens
        instance.skiplist_words = model.skiplist_words
        instance.skiplist = model.skiplist
        instance.query_prefix_id = model.query_prefix_id
        instance.document_prefix_id = model.document_prefix_id
        instance._similarity_fn_name = getattr(model, '_similarity_fn_name', None)
        instance._similarity = getattr(model, '_similarity', None)
        instance._similarity_pairwise = getattr(model, '_similarity_pairwise', None)
        instance.is_hpu_graph_enabled = getattr(model, 'is_hpu_graph_enabled', False)

        # Copy SentenceTransformer attributes
        instance.prompts = getattr(model, 'prompts', {})
        instance.default_prompt_name = getattr(model, 'default_prompt_name', None)
        instance._target_device = getattr(model, '_target_device', None)
        instance.model_card_data = getattr(model, 'model_card_data', None)
        instance.truncate_dim = getattr(model, 'truncate_dim', None)

        # Set up Matryoshka-specific attributes
        instance.matryoshka_dims = sorted(dims)
        instance.max_dim = max(dims)
        instance._hidden_size = instance._get_hidden_size()
        instance._is_modern_bert = instance._check_modern_bert()

        if instance._is_modern_bert:
            logger.info("Detected ModernBert - will remove token_type_ids from inputs")
            instance._patch_for_modern_bert()

        # Create projection heads
        instance.projection_heads = nn.ModuleDict()
        for dim in instance.matryoshka_dims:
            instance.projection_heads[str(dim)] = nn.Linear(
                instance._hidden_size, dim, bias=False
            )
            logger.info(f"Created projection head: {instance._hidden_size} -> {dim}")

        instance._init_projection_heads()
        instance.active_dim = instance.max_dim

        logger.info(f"MatryoshkaColBERT.from_colbert() initialized with dims: {instance.matryoshka_dims}")
        return instance


# Backward compatibility aliases
MatryoshkaColBERTWrapper = MatryoshkaColBERT


# Legacy load function for backward compatibility
def load_pretrained(path: str, **kwargs):
    """Legacy function for backward compatibility."""
    return MatryoshkaColBERT.from_pretrained(path, **kwargs)
