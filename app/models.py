from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
import datetime

# Profile model to extend the built-in User model
class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('employee', 'Employee'),
        ('intern', 'Intern'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='employee')
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"

class WorkConfiguration(models.Model):
    CUTOFF_CHOICES = (
        ('15_30', '15th and 30th of each month'),
        ('weekly', 'Weekly'),
        ('daily', 'Daily'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='work_config')
    hours_per_day = models.DecimalField(max_digits=4, decimal_places=2, default=8.00, help_text="Expected work hours per day")
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Hourly rate in your currency")
    cutoff_type = models.CharField(max_length=10, choices=CUTOFF_CHOICES, default='15_30')
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Additional bonus amount")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Work Configuration'
        verbose_name_plural = 'Work Configurations'
    
    def __str__(self):
        return f"{self.user.username} - {self.hours_per_day}hrs/day @ {self.hourly_rate}/hr"

class Timestamp(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_entry = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.employee.username} - {'Entry' if self.is_entry else 'Exit'} at {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']

class DailyWorkSummary(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    time_in = models.TimeField(null=True, blank=True)
    time_out = models.TimeField(null=True, blank=True)
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    late_minutes = models.IntegerField(default=0)
    late_deduction_minutes = models.IntegerField(default=0)  # After applying the 15-minute rule
    undertime_minutes = models.IntegerField(default=0)
    gross_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    net_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['employee', 'date']
        ordering = ['-date']
        verbose_name = 'Daily Work Summary'
        verbose_name_plural = 'Daily Work Summaries'
    
    def __str__(self):
        return f"{self.employee.username} - {self.date} ({self.total_hours}hrs)"
    
    def calculate_late_deduction(self, late_minutes):
        """
        Calculate late deduction based on the rule:
        1 minute late = 15 minutes deduction
        Additional minutes are added to the 15 minutes
        """
        if late_minutes <= 0:
            return 0
        elif late_minutes == 1:
            return 15
        else:
            return 15 + (late_minutes - 1)
    
    def update_calculations(self):
        """Update all calculations for this daily summary"""
        try:
            work_config = self.employee.work_config
        except WorkConfiguration.DoesNotExist:
            # Create default work config if none exists
            work_config = WorkConfiguration.objects.create(
                user=self.employee,
                hours_per_day=8.00,
                hourly_rate=0.00
            )
        
        # Calculate late deduction
        self.late_deduction_minutes = self.calculate_late_deduction(self.late_minutes)
        
        # Calculate deductions in hours
        total_deduction_minutes = self.late_deduction_minutes + self.undertime_minutes
        deduction_hours = Decimal(total_deduction_minutes) / Decimal(60)
        
        # Calculate gross pay (actual hours worked)
        self.gross_pay = self.total_hours * work_config.hourly_rate
        
        # Calculate deductions amount
        self.deductions = deduction_hours * work_config.hourly_rate
        
        # Calculate net pay
        self.net_pay = self.gross_pay - self.deductions
        
        self.save()

class PayrollPeriod(models.Model):
    PERIOD_TYPE_CHOICES = (
        ('15_30', '15th and 30th'),
        ('weekly', 'Weekly'),
        ('daily', 'Daily'),
    )
    
    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    period_type = models.CharField(max_length=10, choices=PERIOD_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    total_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    total_gross_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    net_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    is_finalized = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['employee', 'start_date', 'end_date']
        ordering = ['-start_date']
        verbose_name = 'Payroll Period'
        verbose_name_plural = 'Payroll Periods'
    
    def __str__(self):
        return f"{self.employee.username} - {self.start_date} to {self.end_date}"
    
    def calculate_totals(self):
        """Calculate totals from daily summaries"""
        daily_summaries = DailyWorkSummary.objects.filter(
            employee=self.employee,
            date__range=[self.start_date, self.end_date]
        )
        
        self.total_hours = sum(summary.total_hours for summary in daily_summaries)
        self.total_gross_pay = sum(summary.gross_pay for summary in daily_summaries)
        self.total_deductions = sum(summary.deductions for summary in daily_summaries)
        
        # Add bonus from work configuration
        try:
            work_config = self.employee.work_config
            self.bonus = work_config.bonus
        except WorkConfiguration.DoesNotExist:
            self.bonus = Decimal('0.00')
        
        self.net_pay = self.total_gross_pay - self.total_deductions + self.bonus
        self.save()