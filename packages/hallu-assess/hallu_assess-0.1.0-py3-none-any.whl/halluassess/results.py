# halluassess/results.py

from dataclasses import dataclass, field
from typing import List, Any


@dataclass
class EvaluationResult:
    """
    Final output returned by halluassess.evaluate()

    This is a stable public contract.
    Do NOT break fields once released.
    """

    # Representative / final answer (usually centroid response)
    text: str

    # All raw model outputs (N samples)
    samples: List[str] = field(default_factory=list)

    # Hallucination score in range [0.0, 1.0]
    hallucination_score: float = 0.0

    # Indices or details of deviating samples
    outliers: List[Any] = field(default_factory=list)

    # Placeholder for future explanation system
    # False for now by design
    explanation: bool = False

    def __repr__(self) -> str:
        return (
            f"EvaluationResult("
            f"hallucination_score={self.hallucination_score:.2f}, "
            f"outliers={len(self.outliers)}, "
            f"samples={len(self.samples)}, "
            f"explanation={self.explanation}"
            f")"
        )