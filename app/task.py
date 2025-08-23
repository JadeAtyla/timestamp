from celery import shared_task
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def clean_pycache_task(self, max_size_mb=10, delete_all=False):
    """
    Celery task for cleaning __pycache__ directories.
    Use this for production deployments with Celery.
    """
    try:
        logger.info('Starting scheduled __pycache__ cleanup task')
        if delete_all:
            call_command('clean_pycache', delete_all=True, verbosity=1)
        else:
            call_command('clean_pycache', max_size=max_size_mb, verbosity=1)
        logger.info('Scheduled __pycache__ cleanup task completed')
        return "PyCache cleanup completed successfully"
    except Exception as exc:
        logger.error(f"PyCache cleanup task failed: {exc}", exc_info=True)
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
