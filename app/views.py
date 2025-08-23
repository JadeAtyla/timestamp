from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from .decorators import role_required
from .models import Timestamp, UserProfile
from .forms import LoginForm, RegistrationForm, CustomPasswordChangeForm, AdminPasswordResetForm

# This new view acts as the landing page router
def landing_page(request):
    """
    Checks if the user is authenticated.
    If so, redirects to the employee dashboard.
    Otherwise, redirects to the login page.
    """
    if request.user.is_authenticated:
        return redirect('employee_dashboard')
    else:
        return redirect('login')

# This view is for employees and interns
@role_required(allowed_roles=['employee', 'intern'])
def employee_dashboard(request):
    """
    Renders the employee dashboard.
    """
    return render(request, 'pages/employee_dashboard.html')

# This view is for admins only
@role_required(allowed_roles=['admin'])
def admin_dashboard(request):
    """
    Renders the admin dashboard with user and timestamp data.
    """
    users_with_timestamps = User.objects.all().prefetch_related('timestamp_set', 'profile')
    
    for user in users_with_timestamps:
        user.last_timestamp = user.timestamp_set.order_by('-timestamp').first()

    context = {
        'users': users_with_timestamps,
    }
    return render(request, 'pages/admin_dashboard.html', context)

# Handles user login
def user_login(request):
    """
    Handles user login.
    """
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                
                # Redirect based on user's role using the profile
                try:
                    if user.profile.role == 'admin':
                        return redirect('admin_dashboard')
                    else:
                        return redirect('employee_dashboard')
                except UserProfile.DoesNotExist:
                    # If no profile exists, create a default one
                    UserProfile.objects.create(user=user, role='employee')
                    return redirect('employee_dashboard')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()
    
    return render(request, 'auth/login.html', {'form': form})

# Handles new user registration
def user_register(request):
    """
    Handles new user registration.
    """
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful! You have been logged in.")
            return redirect('employee_dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = RegistrationForm()
    
    return render(request, 'auth/register.html', {'form': form})

def user_logout(request):
    """
    Logs out the current user.
    """
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

# Password change view for users
@login_required
def change_password(request):
    """
    Allows users to change their own password.
    """
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            
            # Redirect based on user role
            try:
                if request.user.profile.role == 'admin':
                    return redirect('admin_dashboard')
                else:
                    return redirect('employee_dashboard')
            except UserProfile.DoesNotExist:
                return redirect('employee_dashboard')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    return render(request, 'auth/change_password.html', {'form': form})

# Admin password reset view
@role_required(allowed_roles=['admin'])
def admin_reset_password(request, user_id):
    """
    Allows admin to reset any user's password.
    """
    target_user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = AdminPasswordResetForm(target_user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Password for {target_user.username} has been successfully reset!')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminPasswordResetForm(target_user)
    
    context = {
        'form': form,
        'target_user': target_user,
    }
    return render(request, 'auth/admin_reset_password.html', context)

# User detail view for admin
@role_required(allowed_roles=['admin'])
def user_detail(request, user_id):
    """
    Shows detailed view of a user for admin.
    """
    target_user = get_object_or_404(User, id=user_id)
    recent_timestamps = Timestamp.objects.filter(employee=target_user).order_by('-timestamp')[:20]
    
    context = {
        'target_user': target_user,
        'recent_timestamps': recent_timestamps,
    }
    return render(request, 'pages/user_detail.html', context)

# --- API ENDPOINTS FOR FRONTEND ---

@csrf_exempt
def api_get_logs(request):
    """
    API endpoint to get a list of the authenticated user's time logs.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    logs = Timestamp.objects.filter(employee=request.user).order_by('-timestamp').values('timestamp', 'is_entry')
    return JsonResponse(list(logs), safe=False)

@csrf_exempt
def api_create_timestamp(request):
    """
    API endpoint to create a new timestamp for the authenticated user.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    if request.method == 'POST':
        # Get the last log to determine if the new one is an entry or exit
        last_log = Timestamp.objects.filter(employee=request.user).order_by('-timestamp').first()
        is_entry = True
        if last_log and last_log.is_entry:
            is_entry = False

        Timestamp.objects.create(employee=request.user, is_entry=is_entry)
        
        message = "You have successfully punched in." if is_entry else "You have successfully punched out."
        return JsonResponse({'success': True, 'message': message})
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)