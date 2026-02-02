# halluassess/llms/factory.py

from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic

from halluassess.errors import ModelNotSupportedError


def get_llm(
    model: str,
    temperature: float = 0.7,
):
    """
    Return a LangChain Chat LLM for the given model name.

    Model names must be exact (no aliasing).
    API keys are resolved via environment variables.

    Supported providers:
    - OpenAI (gpt-*)
    - Gemini (gemini-*)
    - Claude (claude-*)
    """

    model = model.strip()

    # --------------------
    # OpenAI
    # --------------------
    if model.startswith("gpt-") or model.startswith("o3-"):
        return ChatOpenAI(
            model=model,
            temperature=temperature,
        )

    # --------------------
    # Gemini / Gemma
    # --------------------
    if model.startswith("gemini-") or model.startswith("gemma-"):
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
        )

    # --------------------
    # Anthropic / Claude
    # --------------------
    if model.startswith("claude-"):
        return ChatAnthropic(
            model=model,
            temperature=temperature,
        )

    # --------------------
    # Unsupported
    # --------------------
    raise ModelNotSupportedError(
        f"Model '{model}' is not supported by halluassess."
    )
