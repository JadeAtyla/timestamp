from django.utils import timezone
from django.contrib.auth.models import User
from decimal import Decimal
import datetime
from .models import Timestamp, DailyWorkSummary, WorkConfiguration, PayrollPeriod

def calculate_daily_work_summary(user, date):
    """
    Calculate daily work summary for a specific user and date
    """
    # Get all timestamps for the user on the specific date
    timestamps = Timestamp.objects.filter(
        employee=user,
        timestamp__date=date
    ).order_by('timestamp')
    
    if not timestamps.exists():
        return None
    
    # Initialize values
    time_in = None
    time_out = None
    total_minutes = 0
    
    # Process timestamps in pairs (entry, exit)
    entries = []
    exits = []
    
    for timestamp in timestamps:
        if timestamp.is_entry:
            entries.append(timestamp)
        else:
            exits.append(timestamp)
    
    # Calculate total work time
    work_sessions = []
    for i, entry in enumerate(entries):
        if i < len(exits):
            exit_time = exits[i]
            duration = (exit_time.timestamp - entry.timestamp).total_seconds() / 60
            work_sessions.append({
                'entry': entry.timestamp,
                'exit': exit_time.timestamp,
                'duration': duration
            })
            total_minutes += duration
        else:
            # Entry without exit (still working or forgot to punch out)
            work_sessions.append({
                'entry': entry.timestamp,
                'exit': None,
                'duration': 0
            })
    
    # Set time_in as first entry and time_out as last exit
    if entries:
        time_in = entries[0].timestamp.time()
    if exits:
        time_out = exits[-1].timestamp.time()
    
    # Calculate total hours
    total_hours = Decimal(str(total_minutes / 60)).quantize(Decimal('0.01'))
    
    # Get work configuration
    try:
        work_config = user.work_config
    except WorkConfiguration.DoesNotExist:
        work_config = WorkConfiguration.objects.create(
            user=user,
            hours_per_day=8.00,
            hourly_rate=0.00
        )
    
    # Calculate late minutes (assuming work starts at 8:00 AM)
    expected_start_time = datetime.time(8, 0)  # 8:00 AM
    late_minutes = 0
    
    if time_in and time_in > expected_start_time:
        start_datetime = datetime.datetime.combine(date, expected_start_time)
        actual_datetime = datetime.datetime.combine(date, time_in)
        late_minutes = int((actual_datetime - start_datetime).total_seconds() / 60)
    
    # Calculate undertime minutes
    expected_hours = work_config.hours_per_day
    expected_minutes = float(expected_hours) * 60
    undertime_minutes = max(0, int(expected_minutes - total_minutes))
    
    # Get or create daily summary
    daily_summary, created = DailyWorkSummary.objects.get_or_create(
        employee=user,
        date=date,
        defaults={
            'time_in': time_in,
            'time_out': time_out,
            'total_hours': total_hours,
            'late_minutes': late_minutes,
            'undertime_minutes': undertime_minutes,
        }
    )
    
    if not created:
        # Update existing summary
        daily_summary.time_in = time_in
        daily_summary.time_out = time_out
        daily_summary.total_hours = total_hours
        daily_summary.late_minutes = late_minutes
        daily_summary.undertime_minutes = undertime_minutes
        daily_summary.save()
    
    # Update calculations
    daily_summary.update_calculations()
    
    return daily_summary

def generate_payroll_period(user, start_date, end_date):
    """
    Generate payroll period for a user between two dates
    """
    try:
        work_config = user.work_config
    except WorkConfiguration.DoesNotExist:
        work_config = WorkConfiguration.objects.create(
            user=user,
            hours_per_day=8.00,
            hourly_rate=0.00
        )
    
    # Calculate daily summaries for all days in the period
    current_date = start_date
    while current_date <= end_date:
        calculate_daily_work_summary(user, current_date)
        current_date += datetime.timedelta(days=1)
    
    # Get or create payroll period
    payroll_period, created = PayrollPeriod.objects.get_or_create(
        employee=user,
        start_date=start_date,
        end_date=end_date,
        defaults={
            'period_type': work_config.cutoff_type,
        }
    )
    
    if not created:
        payroll_period.period_type = work_config.cutoff_type
        payroll_period.save()
    
    # Calculate totals
    payroll_period.calculate_totals()
    
    return payroll_period

def get_current_payroll_dates(cutoff_type):
    """
    Get current payroll period dates based on cutoff type
    """
    today = timezone.now().date()
    
    if cutoff_type == '15_30':
        if today.day <= 15:
            start_date = today.replace(day=1)
            end_date = today.replace(day=15)
        else:
            start_date = today.replace(day=16)
            # Get last day of month
            if today.month == 12:
                next_month = today.replace(year=today.year + 1, month=1, day=1)
            else:
                next_month = today.replace(month=today.month + 1, day=1)
            end_date = next_month - datetime.timedelta(days=1)
    
    elif cutoff_type == 'weekly':
        # Get Monday of current week
        days_since_monday = today.weekday()
        start_date = today - datetime.timedelta(days=days_since_monday)
        end_date = start_date + datetime.timedelta(days=6)
    
    else:  # daily
        start_date = today
        end_date = today
    
    return start_date, end_date

def update_user_daily_summaries(user, num_days=30):
    """
    Update daily summaries for a user for the last N days
    """
    today = timezone.now().date()
    for i in range(num_days):
        date = today - datetime.timedelta(days=i)
        calculate_daily_work_summary(user, date)