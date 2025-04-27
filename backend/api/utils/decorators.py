import asyncio
from functools import wraps
from django.conf import settings

def with_transaction(fn):
    """
    Run fn inside a pymongo transaction. Passes 'session' kwarg.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        client = settings.MONGODB_CLIENT
        with client.start_session() as session:
            session.start_transaction()
            try:
                result = fn(*args, session=session, **kwargs)
                session.commit_transaction()
                return result
            except Exception:
                session.abort_transaction()
                raise
    return wrapper

def run_async(fn):
    """
    Synchronous wrapper for an async function.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        return asyncio.run(fn(*args, **kwargs))
    return wrapper