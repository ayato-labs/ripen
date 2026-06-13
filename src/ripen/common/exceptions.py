class RipenError(Exception):
    """Base exception for Ripen."""

    pass


class DatabaseError(RipenError):
    """Raised when a database operation fails."""

    pass


class DatabaseLockedError(DatabaseError):
    """Raised when the database remains locked after all retries."""

    pass


class LockTimeoutError(RipenError):
    """Raised when a cross-process lock cannot be acquired within the timeout."""

    pass


class ValidationError(RipenError):
    """Raised when input data fails validation."""

    pass


class ResourceNotFoundError(RipenError):
    """Raised when a requested resource (snapshot, file, entity) is not found."""

    pass


class SecurityError(RipenError):
    """Raised when a security-sensitive operation (like path traversal) is blocked."""

    pass
