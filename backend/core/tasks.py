"""Celery tasks for core (playground maintenance)."""

import logging

from celery import shared_task

from core.application.playground_service import cleanup_expired_playground_sessions

logger = logging.getLogger(__name__)


@shared_task(name="core.tasks.cleanup_expired_playground_sessions")
def cleanup_expired_playground_sessions_task() -> int:
    removed = cleanup_expired_playground_sessions()
    if removed:
        logger.info("Removed %s expired playground session(s)", removed)
    return removed
