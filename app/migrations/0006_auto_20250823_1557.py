from django.db import migrations
from django.contrib.auth.models import User

def create_user_profiles(apps, schema_editor):
    UserProfile = apps.get_model('app', 'UserProfile')
    User = apps.get_model('auth', 'User')
    
    for user in User.objects.all():
        if not hasattr(user, 'profile'):
            # Determine role based on existing permissions
            if user.is_superuser and user.is_staff:
                role = 'admin'
            elif not user.is_superuser and user.is_staff:
                role = 'employee'
            else:
                role = 'intern'
            
            UserProfile.objects.get_or_create(user=user, defaults={'role': role})

def reverse_create_profiles(apps, schema_editor):
    UserProfile = apps.get_model('app', 'UserProfile')
    UserProfile.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('app', '0004_user_alter_timestamp_employee_delete_profile'),
    ]

    operations = [
        migrations.RunPython(create_user_profiles, reverse_create_profiles),
    ]