# Optional: Create a management command to set up default work configs
# app/management/commands/setup_work_configs.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app.models import WorkConfiguration

class Command(BaseCommand):
    help = 'Create default work configurations for existing users'

    def handle(self, *args, **options):
        users_without_config = User.objects.filter(work_config__isnull=True)
        
        for user in users_without_config:
            WorkConfiguration.objects.create(
                user=user,
                hours_per_day=8.00,
                hourly_rate=15.00,  # Set your default rate
                cutoff_type='15_30'
            )
            self.stdout.write(
                self.style.SUCCESS(f'Created work config for {user.username}')
            )