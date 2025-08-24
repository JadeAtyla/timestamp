from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm, SetPasswordForm
from django.contrib.auth.models import User
from .models import UserProfile

class LoginForm(AuthenticationForm):
    """
    A form for user login - inherits from AuthenticationForm properly.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
            'id': 'username'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
            'id': 'password'
        })

class RegistrationForm(UserCreationForm):
    """
    A form for new user registration with a role choice.
    """
    ROLE_CHOICES = (
        ('employee', 'Employee'),
        ('intern', 'Intern'),
    )
    
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        role = self.cleaned_data['role']
        
        # Set Django's built-in permissions based on the role
        if role == 'employee':
            user.is_superuser = False
            user.is_staff = True
        elif role == 'intern':
            user.is_superuser = False
            user.is_staff = False
        
        if commit:
            user.save()
            # Create the user profile with the role
            UserProfile.objects.create(user=user, role=role)
        
        return user

class CustomPasswordChangeForm(PasswordChangeForm):
    """
    Custom password change form with styling
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add CSS classes to all password fields
        for field_name in ['old_password', 'new_password1', 'new_password2']:
            self.fields[field_name].widget.attrs.update({
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm'
            })

class AdminPasswordResetForm(SetPasswordForm):
    """
    Form for admin to reset user passwords (doesn't require old password)
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add CSS classes to password fields
        for field_name in ['new_password1', 'new_password2']:
            self.fields[field_name].widget.attrs.update({
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm'
            })