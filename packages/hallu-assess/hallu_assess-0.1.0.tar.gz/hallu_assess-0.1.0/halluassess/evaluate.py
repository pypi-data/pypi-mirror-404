# halluassess/evaluate.py

from typing import Optional

from halluassess.llms.factory import get_llm
from halluassess.prompts.builder import build_messages
from halluassess.sampling.runner import run_sampling
from halluassess.embeddings.encoder import EmbeddingEncoder
from halluassess.scoring.similarity import analyze_embeddings
from halluassess.results import EvaluationResult
from halluassess.errors import GenerationError


def evaluate(
    *,
    system: Optional[str] = None,
    context: Optional[str] = None,
    user: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    samples: int = 4,
) -> EvaluationResult:
    """
    Evaluate hallucination likelihood for a prompt by measuring
    semantic instability across multiple generations.

    Args:
        system: Optional system prompt
        context: Optional grounding / RAG context (string)
        user: User prompt (required)
        model: Model name (required)
        temperature: Sampling temperature (default: 0.7)
        samples: Number of generations to sample (default: 4)

    Returns:
        EvaluationResult
    """

    if not user:
        raise ValueError("`user` prompt is required")

    if not model:
        raise ValueError("`model` is required")

    if samples < 1:
        raise ValueError("`samples` must be >= 1")

    # 1Build LLM
    llm = get_llm(model=model, temperature=temperature)

    # 2Build prompt messages
    messages = build_messages(
        system=system,
        context=context,
        user=user,
    )

    # 3Sample multiple generations
    try:
        generations = run_sampling(
            llm=llm,
            messages=messages,
            n=samples,
        )
    except Exception as e:
        raise GenerationError(str(e))

    # 4Embed generations
    encoder = EmbeddingEncoder()
    embeddings = encoder.encode(generations)

    # 5Analyze semantic deviation
    hallucination_score, outliers = analyze_embeddings(embeddings)

    # 6Choose representative text (centroid-nearest)
    if outliers and len(outliers) < len(generations):
        # Prefer non-outlier sample if available
        representative_idx = next(
            i for i in range(len(generations)) if i not in outliers
        )
    else:
        representative_idx = 0

    representative_text = generations[representative_idx]

    # 7Return stable result object
    return EvaluationResult(
        text=representative_text,
        samples=generations,
        hallucination_score=hallucination_score,
        outliers=outliers,
        explanation=False,  # placeholder (V2)
    )
