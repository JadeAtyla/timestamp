from django.shortcuts import redirect
from django.contrib.auth.decorators import user_passes_test
from .models import UserProfile

def role_required(allowed_roles=None):
    """
    Decorator to check if a user belongs to a specific role using UserProfile.
    
    Args:
        allowed_roles (list): A list of roles that are allowed to access the view.
                              'admin', 'employee', or 'intern'
    """
    if allowed_roles is None:
        allowed_roles = []
    
    def check_user(user):
        # A user must be authenticated
        if not user.is_authenticated:
            return False

        try:
            user_role = user.profile.role
        except UserProfile.DoesNotExist:
            # If no profile exists, create a default one
            UserProfile.objects.create(user=user, role='employee')
            user_role = 'employee'

        # Check if user's role is in allowed roles
        return user_role in allowed_roles

    return user_passes_test(check_user, login_url='/login/')