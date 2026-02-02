# halluassess/scoring/similarity.py

from typing import List, Tuple
import numpy as np


def compute_centroid(embeddings: np.ndarray) -> np.ndarray:
    """
    Compute centroid of embeddings.
    """
    return np.mean(embeddings, axis=0)


def compute_distances(
    embeddings: np.ndarray,
    centroid: np.ndarray,
) -> np.ndarray:
    """
    Compute cosine distance from centroid.
    Assumes embeddings are L2-normalized.
    """
    similarities = embeddings @ centroid
    distances = 1.0 - similarities
    return distances


def detect_outliers(
    distances: np.ndarray,
    k: float = 1.0,
    min_samples: int = 3,
) -> List[int]:
    """
    Detect outliers using relative deviation.

    Outlier rule:
        distance > mean + k * std

    Safeguards:
    - If samples < min_samples, return no outliers
    - If std == 0, return no outliers
    """

    n = len(distances)
    if n < min_samples:
        return []

    mean = float(np.mean(distances))
    std = float(np.std(distances))

    if std == 0.0:
        return []

    threshold = mean + k * std

    return [i for i, d in enumerate(distances) if d > threshold]


def hallucination_score(
    distances: np.ndarray,
) -> float:
    """
    Hallucination score = mean semantic deviation.

    Range: [0, 1]
    """
    score = float(np.mean(distances))
    return min(max(score, 0.0), 1.0)


def analyze_embeddings(
    embeddings: np.ndarray,
    outlier_k: float = 1.0,
) -> Tuple[float, List[int]]:
    """
    Full analysis pipeline.

    Returns:
        hallucination_score (float),
        outlier_indices (List[int])
    """
    centroid = compute_centroid(embeddings)
    distances = compute_distances(embeddings, centroid)
    outliers = detect_outliers(distances, k=outlier_k)
    score = hallucination_score(distances)
    return score, outliers
