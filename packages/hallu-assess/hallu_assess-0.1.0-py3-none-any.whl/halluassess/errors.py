# halluassess/errors.py

class HalluAssessError(Exception):
    """Base exception for halluassess."""
    pass


class ModelNotSupportedError(HalluAssessError):
    """Raised when a model name is not supported."""
    pass


class GenerationError(HalluAssessError):
    """Raised when LLM generation fails."""
    pass
