import asyncio
from functools import wraps
from django.conf import settings


def with_transaction(fn):
    """
    Start a client session + transaction if none was passed in.
    If `session` is given in kwargs, just call `fn` directly.
    """
    @wraps(fn)
    def wrapper(*args, session=None, **kwargs):
        # If a parent already supplied a session, just run.
        if session is not None:
            return fn(*args, session=session, **kwargs)

        # Otherwise, start our own session + transaction
        client = settings.MONGODB_CLIENT
        with client.start_session() as s:
            s.start_transaction()
            try:
                result = fn(*args, session=s, **kwargs)
            except Exception:
                s.abort_transaction()
                raise
            else:
                s.commit_transaction()
                return result

    return wrapper

def run_async(fn):
    """
    Wrap an async view and run its coroutine on the loop, returning the actual Response.
    """
    @wraps(fn)
    def wrapper(self, request, *args, **kwargs):
        # asyncio.run returns whatever the async fn returned
        return asyncio.run(fn(self, request, *args, **kwargs))
    return wrapper