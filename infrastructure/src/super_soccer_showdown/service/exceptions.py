class DomainError(Exception):
    """Base domain exception."""


class InvalidLineupError(DomainError):
    """Raised when lineup settings are invalid."""


class TeamGenerationError(DomainError):
    """Raised when a team cannot be generated."""
