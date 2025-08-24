from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q, Sum, Avg
import json
import datetime

from .decorators import role_required
from .models import Timestamp, UserProfile, WorkConfiguration, DailyWorkSummary, PayrollPeriod
from .forms import LoginForm, RegistrationForm, CustomPasswordChangeForm, AdminPasswordResetForm, WorkConfigurationForm
from .utils import calculate_daily_work_summary, generate_payroll_period, get_current_payroll_dates, update_user_daily_summaries

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
    Renders the employee dashboard with payroll information.
    """
    # Update daily summaries for the last 30 days
    update_user_daily_summaries(request.user, 30)
    
    # Get current payroll information
    try:
        work_config = request.user.work_config
    except WorkConfiguration.DoesNotExist:
        work_config = WorkConfiguration.objects.create(
            user=request.user,
            hours_per_day=8.00,
            hourly_rate=0.00
        )
    
    # Get current payroll period
    start_date, end_date = get_current_payroll_dates(work_config.cutoff_type)
    current_payroll = generate_payroll_period(request.user, start_date, end_date)
    
    # Get recent daily summaries
    recent_summaries = DailyWorkSummary.objects.filter(
        employee=request.user,
        date__range=[start_date, end_date]
    ).order_by('-date')[:10]
    
    # Get all payroll periods
    all_payrolls = PayrollPeriod.objects.filter(
        employee=request.user
    ).order_by('-start_date')[:5]
    
    context = {
        'work_config': work_config,
        'current_payroll': current_payroll,
        'recent_summaries': recent_summaries,
        'all_payrolls': all_payrolls,
    }
    return render(request, 'pages/employee_dashboard.html', context)

# This view is for admins only
@role_required(allowed_roles=['admin'])
def admin_dashboard(request):
    """
    Renders the admin dashboard with user and timestamp data.
    """
    users_with_timestamps = User.objects.all().prefetch_related('timestamp_set', 'profile', 'work_config')
    
    for user in users_with_timestamps:
        user.last_timestamp = user.timestamp_set.order_by('-timestamp').first()
        
        # Get today's work summary
        today = timezone.now().date()
        today_summary = DailyWorkSummary.objects.filter(
            employee=user,
            date=today
        ).first()
        user.today_summary = today_summary

    context = {
        'users': users_with_timestamps,
    }
    return render(request, 'pages/admin_dashboard.html', context)

# Work configuration management
@role_required(allowed_roles=['admin'])
def edit_work_config(request, user_id):
    """
    Edit work configuration for a user
    """
    target_user = get_object_or_404(User, id=user_id)
    
    try:
        work_config = target_user.work_config
    except WorkConfiguration.DoesNotExist:
        work_config = WorkConfiguration.objects.create(
            user=target_user,
            hours_per_day=8.00,
            hourly_rate=0.00
        )
    
    if request.method == 'POST':
        form = WorkConfigurationForm(request.POST, instance=work_config)
        if form.is_valid():
            form.save()
            messages.success(request, f'Work configuration updated for {target_user.username}!')
            return redirect('user_detail', user_id=user_id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = WorkConfigurationForm(instance=work_config)
    
    context = {
        'form': form,
        'target_user': target_user,
        'work_config': work_config,
    }
    return render(request, 'pages/edit_work_config.html', context)

# Payroll management
@role_required(allowed_roles=['admin'])
def user_payroll(request, user_id):
    """
    View user's payroll information
    """
    target_user = get_object_or_404(User, id=user_id)
    
    # Update daily summaries for the last 30 days
    update_user_daily_summaries(target_user, 30)
    
    # Get payroll periods
    payroll_periods = PayrollPeriod.objects.filter(
        employee=target_user
    ).order_by('-start_date')
    
    # Get recent daily summaries
    recent_summaries = DailyWorkSummary.objects.filter(
        employee=target_user
    ).order_by('-date')[:30]
    
    context = {
        'target_user': target_user,
        'payroll_periods': payroll_periods,
        'recent_summaries': recent_summaries,
    }
    return render(request, 'pages/user_payroll.html', context)

# Generate payroll
@role_required(allowed_roles=['admin'])
def generate_payroll(request, user_id):
    """
    Generate payroll period for a user
    """
    target_user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        start_date = datetime.datetime.strptime(request.POST.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(request.POST.get('end_date'), '%Y-%m-%d').date()
        
        payroll_period = generate_payroll_period(target_user, start_date, end_date)
        messages.success(request, f'Payroll generated for {target_user.username} ({start_date} to {end_date})')
        
        return redirect('user_payroll', user_id=user_id)
    
    return redirect('user_payroll', user_id=user_id)

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
                    WorkConfiguration.objects.create(user=user, hours_per_day=8.00, hourly_rate=0.00)
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
    
    # Get work configuration
    try:
        work_config = target_user.work_config
    except WorkConfiguration.DoesNotExist:
        work_config = WorkConfiguration.objects.create(
            user=target_user,
            hours_per_day=8.00,
            hourly_rate=0.00
        )
    
    # Get recent daily summaries
    recent_summaries = DailyWorkSummary.objects.filter(
        employee=target_user
    ).order_by('-date')[:10]
    
    # Get current payroll info
    start_date, end_date = get_current_payroll_dates(work_config.cutoff_type)
    current_payroll = generate_payroll_period(target_user, start_date, end_date)
    
    context = {
        'target_user': target_user,
        'recent_timestamps': recent_timestamps,
        'work_config': work_config,
        'recent_summaries': recent_summaries,
        'current_payroll': current_payroll,
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

        timestamp_obj = Timestamp.objects.create(employee=request.user, is_entry=is_entry)
        
        # Update daily work summary for today
        today = timezone.now().date()
        calculate_daily_work_summary(request.user, today)
        
        message = "You have successfully punched in." if is_entry else "You have successfully punched out."
        return JsonResponse({'success': True, 'message': message})
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def api_get_payroll_summary(request):
    """
    API endpoint to get payroll summary for the authenticated user.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        work_config = request.user.work_config
    except WorkConfiguration.DoesNotExist:
        return JsonResponse({'error': 'Work configuration not found'}, status=404)
    
    # Get current payroll period
    start_date, end_date = get_current_payroll_dates(work_config.cutoff_type)
    current_payroll = generate_payroll_period(request.user, start_date, end_date)
    
    data = {
        'period_start': start_date.strftime('%Y-%m-%d'),
        'period_end': end_date.strftime('%Y-%m-%d'),
        'total_hours': float(current_payroll.total_hours),
        'gross_pay': float(current_payroll.total_gross_pay),
        'deductions': float(current_payroll.total_deductions),
        'bonus': float(current_payroll.bonus),
        'net_pay': float(current_payroll.net_pay),
        'hourly_rate': float(work_config.hourly_rate),
    }
    
    return JsonResponse(data)