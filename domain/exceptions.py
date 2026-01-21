"""
Domain exceptions.
"""


class DomainError(Exception):
    """Base exception for domain errors."""
    pass


class InvalidDurationError(DomainError):
    """Raised when duration is invalid."""
    pass


class InvalidSceneTypeError(DomainError):
    """Raised when scene type is invalid."""
    pass


class InvalidShotTypeError(DomainError):
    """Raised when shot type is invalid."""
    pass


class InvalidGenerationMethodError(DomainError):
    """Raised when generation method is invalid."""
    pass


class CharacterNotFoundError(DomainError):
    """Raised when referenced character is not found."""
    pass
