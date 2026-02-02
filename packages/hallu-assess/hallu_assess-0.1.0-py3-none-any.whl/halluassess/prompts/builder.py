# halluassess/prompts/builder.py

from typing import List, Optional

from langchain_core.messages import SystemMessage, HumanMessage


def build_messages(
    system: Optional[str] = None,
    context: Optional[str] = None,
    user: Optional[str] = None,
) -> List:
    """
    Build LangChain messages in the order:
    system → context → user

    - system: high-level role / instruction
    - context: grounding information (RAG)
    - user: actual user query
    """

    if not user:
        raise ValueError("user prompt is required")

    messages = []

    if system:
        messages.append(SystemMessage(content=str(system)))

    if context:
        messages.append(SystemMessage(content=str(context)))

    messages.append(HumanMessage(content=str(user)))

    return messages
