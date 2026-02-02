# halluassess/embeddings/encoder.py

from typing import List
import numpy as np

from sentence_transformers import SentenceTransformer


class EmbeddingEncoder:
    """
    Local embedding encoder using all-MiniLM-L6-v2.

    - CPU only
    - No API keys
    - Deterministic
    - Fast
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name, device="cpu")

    def encode(self, texts: List[str]) -> np.ndarray:
        """
        Encode a list of texts into embeddings.

        Args:
            texts: List of strings

        Returns:
            np.ndarray of shape (len(texts), embedding_dim)
        """

        if not texts:
            raise ValueError("texts must be a non-empty list")

        # Ensure clean strings
        texts = [str(t).strip() for t in texts]

        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,  # VERY IMPORTANT
        )

        return embeddings