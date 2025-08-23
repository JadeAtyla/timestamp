import threading
import time
import logging
from django.conf import settings
from django.core.management import call_command


logger = logging.getLogger(__name__)


class PyCacheCleanerMiddleware:
    """
    Production-ready middleware that periodically cleans __pycache__ directories.
    Includes proper error handling, logging, and safety checks.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.last_cleanup = 0
        self.cleanup_interval = getattr(settings, 'PYCACHE_CLEANUP_INTERVAL', 3600)  # 1 hour
        self.max_size_mb = getattr(settings, 'PYCACHE_MAX_SIZE_MB', 10)
        self.delete_all = getattr(settings, 'PYCACHE_DELETE_ALL', False)
        self.enabled = getattr(settings, 'PYCACHE_CLEANER_ENABLED', settings.DEBUG)
        self.cleanup_running = False
        
    def __call__(self, request):
        # Check if cleanup should run
        if (self.enabled and 
            not self.cleanup_running and 
            (time.time() - self.last_cleanup) > self.cleanup_interval):
            
            # Run cleanup in background thread
            threading.Thread(target=self._cleanup_pycache, daemon=True).start()
            self.last_cleanup = time.time()
        
        response = self.get_response(request)
        return response
    
    def _cleanup_pycache(self):
        """Run the cleanup command in background with proper error handling."""
        if self.cleanup_running:
            return
            
        self.cleanup_running = True
        try:
            logger.info('Starting automatic __pycache__ cleanup')
            if self.delete_all:
                call_command('clean_pycache', delete_all=True, verbosity=0)
            else:
                call_command('clean_pycache', max_size=self.max_size_mb, verbosity=0)
            logger.info('Automatic __pycache__ cleanup completed')
        except Exception as e:
            logger.error(f"PyCache cleanup failed: {e}", exc_info=True)
        finally:
            self.cleanup_running = False