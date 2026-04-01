"""
Observability — Langfuse v3 (correct API)
==========================================
Uses the @observe decorator from langfuse.decorators
which is the correct API for langfuse>=2.0.0 / v3.

DO NOT use Langfuse().trace() — that method does not exist in v3.
The correct pattern is @observe() decorator + langfuse_context.

Free at https://cloud.langfuse.com
Add to Render env vars:
  LANGFUSE_PUBLIC_KEY=pk-lf-...
  LANGFUSE_SECRET_KEY=sk-lf-...
  LANGFUSE_HOST=https://cloud.langfuse.com

App works fine without these — observability is silently disabled.
"""

import logging
import os
from config import get_settings

logger = logging.getLogger(__name__)


def _init_langfuse():
    """
    Initialize Langfuse once at startup.
    Sets environment variables so the @observe decorator picks them up automatically.
    Returns True if configured, False if not.
    """
    s = get_settings()

    if not s.langfuse_public_key or not s.langfuse_secret_key:
        return False

    try:
        # Set env vars — the @observe decorator reads these automatically
        os.environ["LANGFUSE_PUBLIC_KEY"]  = s.langfuse_public_key
        os.environ["LANGFUSE_SECRET_KEY"]  = s.langfuse_secret_key
        os.environ["LANGFUSE_HOST"]        = s.langfuse_host

        # Verify the import works
        from langfuse import observe  # noqa
        logger.info("Langfuse observability initialized ✓")
        return True

    except ImportError:
        logger.warning("langfuse package not installed — observability disabled")
        return False
    except Exception as e:
        logger.warning(f"Langfuse init failed (non-critical): {e}")
        return False


# Initialize on module load
_ENABLED = _init_langfuse()


def is_enabled() -> bool:
    return _ENABLED


def get_observe_decorator():
    """
    Returns the @observe decorator if Langfuse is configured.
    Returns a no-op decorator if not configured.

    Usage:
        from observability import get_observe_decorator
        observe = get_observe_decorator()

        @observe()
        async def my_function():
            ...
    """
    if not _ENABLED:
        # Return a no-op decorator that does nothing
        def noop_decorator(*args, **kwargs):
            def wrapper(func):
                return func
            # Handle both @noop_decorator and @noop_decorator()
            if len(args) == 1 and callable(args[0]):
                return args[0]
            return wrapper
        return noop_decorator

    try:
        from langfuse.decorators import observe
        return observe
    except Exception:
        def noop_decorator(*args, **kwargs):
            def wrapper(func):
                return func
            if len(args) == 1 and callable(args[0]):
                return args[0]
            return wrapper
        return noop_decorator


def update_current_observation(metadata: dict):
    """
    Add metadata to the current Langfuse observation.
    Call this from inside an @observe decorated function.
    Silently does nothing if Langfuse not configured.
    """
    if not _ENABLED:
        return
    try:
        from langfuse.decorators import langfuse_context
        langfuse_context.update_current_observation(metadata=metadata)
    except Exception as e:
        logger.debug(f"Langfuse update_current_observation failed (non-critical): {e}")


def flush():
    """Flush all pending Langfuse events. Call on app shutdown."""
    if not _ENABLED:
        return
    try:
        from langfuse import get_client
        get_client().flush()
    except Exception as e:
        logger.debug(f"Langfuse flush failed (non-critical): {e}")