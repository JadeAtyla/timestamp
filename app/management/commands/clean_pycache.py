import os
import shutil
import logging
from django.core.management.base import BaseCommand
from django.conf import settings


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean __pycache__ directories when they exceed specified size'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-size',
            type=float,
            default=getattr(settings, 'PYCACHE_MAX_SIZE_MB', 10.0),
            help='Maximum size in MB before cleaning (default: from settings or 10 MB)'
        )
        parser.add_argument(
            '--path',
            type=str,
            default=None,
            help='Specific path to check (default: project root)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
        parser.add_argument(
            '--force-production',
            action='store_true',
            help='Allow running in production (use with caution)'
        )
        parser.add_argument(
            '--delete-all',
            action='store_true',
            help='Delete all __pycache__ directories regardless of size'
        )

    def handle(self, *args, **options):
        # Production safety check
        if not settings.DEBUG and not options['force_production']:
            if not getattr(settings, 'PYCACHE_CLEANER_ENABLED', False):
                self.stdout.write(
                    self.style.ERROR(
                        'PyCache cleaner is disabled in production. '
                        'Set PYCACHE_CLEANER_ENABLED=True in settings or use --force-production'
                    )
                )
                return

        max_size_bytes = options['max_size'] * 1024 * 1024  # Convert MB to bytes
        base_path = options['path'] or settings.BASE_DIR
        dry_run = options['dry_run']
        delete_all = options['delete_all'] or getattr(settings, 'PYCACHE_DELETE_ALL', False)
        
        total_cleaned = 0
        total_size_cleaned = 0
        
        self.stdout.write(
            self.style.SUCCESS(f'Scanning for __pycache__ directories in: {base_path}')
        )
        
        if delete_all:
            self.stdout.write(f'Mode: DELETE ALL __pycache__ directories (ignoring size)')
        else:
            self.stdout.write(f'Maximum size threshold: {options["max_size"]} MB')
            
        self.stdout.write(f'Environment: {"DEBUG" if settings.DEBUG else "PRODUCTION"}')
        
        # Get excluded paths from settings
        excluded_paths = getattr(settings, 'PYCACHE_EXCLUDED_PATHS', [])
        
        for root, dirs, files in os.walk(base_path):
            # Skip excluded paths
            if any(excluded_path in root for excluded_path in excluded_paths):
                continue
                
            if '__pycache__' in dirs:
                pycache_path = os.path.join(root, '__pycache__')
                size = self.get_directory_size(pycache_path)
                size_mb = size / (1024 * 1024)
                
                # Delete if: delete_all is True OR size exceeds threshold
                should_delete = delete_all or size > max_size_bytes
                    
                if should_delete:
                    if dry_run:
                        reason = "all directories" if delete_all else f"size {size_mb:.2f} MB > {options['max_size']} MB"
                        self.stdout.write(
                            self.style.WARNING(
                                f'Would delete: {pycache_path} ({size_mb:.2f} MB) - {reason}'
                            )
                        )
                    else:
                        try:
                            shutil.rmtree(pycache_path)
                            reason = "exists" if delete_all else f"size {size_mb:.2f} MB"
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'Deleted: {pycache_path} ({size_mb:.2f} MB) - {reason}'
                                )
                            )
                            logger.info(f'Deleted __pycache__ directory: {pycache_path} ({size_mb:.2f} MB)')
                            total_cleaned += 1
                            total_size_cleaned += size
                        except OSError as e:
                            error_msg = f'Failed to delete {pycache_path}: {e}'
                            self.stdout.write(self.style.ERROR(error_msg))
                            logger.error(error_msg)
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS('Dry run completed. No files were actually deleted.')
            )
        else:
            total_size_mb = total_size_cleaned / (1024 * 1024)
            result_msg = (
                f'Cleaning completed. Deleted {total_cleaned} directories, '
                f'freed {total_size_mb:.2f} MB of space.'
            )
            self.stdout.write(self.style.SUCCESS(result_msg))
            logger.info(result_msg)

    def get_directory_size(self, path):
        """Calculate the total size of a directory."""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except (OSError, FileNotFoundError):
                        continue
        except (OSError, FileNotFoundError):
            pass
        return total_size
