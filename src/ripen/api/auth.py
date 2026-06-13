import os
from contextvars import ContextVar
import getpass

from ripen.common.utils import get_logger

logger = get_logger("auth")

# Context variable to hold the authenticated account name for the current request/task
current_user: ContextVar[str | None] = ContextVar("current_user", default=None)
in_http_request: ContextVar[bool] = ContextVar("in_http_request", default=False)


def get_current_user() -> str:
    """
    Returns the account name for the current context.
    In MVP phase, this always returns a default user (RIPEN_ACCOUNT or OS username).
    """
    user = current_user.get()
    if user:
        return user

    # Default fallback for MVP
    return os.environ.get("RIPEN_ACCOUNT") or os.environ.get(
        "SHARED_MEMORY_ACCOUNT", getpass.getuser()
    )
