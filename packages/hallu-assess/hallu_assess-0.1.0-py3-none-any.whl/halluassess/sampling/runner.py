# halluassess/sampling/runner.py

from typing import List
import time

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage

from halluassess.errors import GenerationError


def run_sampling(
    llm: BaseChatModel,
    messages: List[BaseMessage],
    n: int = 4,
    sleep: float = 0.0,
) -> List[str]:
    """
    Run the same prompt multiple times against the same LLM.

    Args:
        llm: LangChain chat model (ChatOpenAI, ChatGoogleGenerativeAI, etc.)
        messages: Prompt messages (system → context → user)
        n: Number of samples to generate
        sleep: Optional delay between calls (seconds)

    Returns:
        List[str]: list of generated texts
    """

    if n < 1:
        raise ValueError("n must be >= 1")

    outputs: List[str] = []

    for i in range(n):
        try:
            response = llm.invoke(messages)
            text = response.content

            if not isinstance(text, str):
                text = str(text)

            outputs.append(text.strip())

        except Exception as e:
            raise GenerationError(
                f"Sampling failed at iteration {i}: {str(e)}"
            )

        if sleep > 0 and i < n - 1:
            time.sleep(sleep)

    return outputs
