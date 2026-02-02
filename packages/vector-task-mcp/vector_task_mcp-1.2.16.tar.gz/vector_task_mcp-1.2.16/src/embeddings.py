"""
Embedding Model Module
======================

Provides sentence transformer embedding functionality for semantic task search.
"""

from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingModel:
    """Wrapper for sentence transformer embedding model."""

    def __init__(self, model_name: str):
        """
        Initialize embedding model.

        Args:
            model_name: HuggingFace model name (e.g., 'sentence-transformers/all-MiniLM-L6-v2')
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def encode(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Encode text to embedding vector(s).

        Args:
            text: Single text string or list of texts

        Returns:
            Numpy array of embeddings (1D for single text, 2D for list)
        """
        embeddings = self.model.encode(text, convert_to_numpy=True)

        # Ensure float32 for sqlite-vec compatibility
        return embeddings.astype(np.float32)

    def encode_single(self, text: str) -> np.ndarray:
        """
        Encode single text to embedding vector.

        Args:
            text: Single text string

        Returns:
            Numpy array of embedding (1D float32)
        """
        return self.encode(text)

    def get_embedding_dim(self) -> int:
        """Get embedding dimension."""
        return self.model.get_sentence_embedding_dimension()


def get_embedding_model(model_name: str) -> EmbeddingModel:
    """
    Factory function to get embedding model instance.

    Args:
        model_name: HuggingFace model name

    Returns:
        Initialized EmbeddingModel instance
    """
    return EmbeddingModel(model_name)