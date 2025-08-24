from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import UserProfile, Timestamp, WorkConfiguration, DailyWorkSummary, PayrollPeriod

# Inline for UserProfile to show in User admin
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

# Inline for WorkConfiguration to show in User admin
class WorkConfigurationInline(admin.StackedInline):
    model = WorkConfiguration
    can_delete = False
    verbose_name_plural = 'Work Configuration'
    extra = 0

# Extend the existing User Admin
class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline, WorkConfigurationInline)
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role']
    list_filter = ['role']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']

@admin.register(Timestamp)
class TimestampAdmin(admin.ModelAdmin):
    list_display = ['employee', 'timestamp', 'is_entry']
    list_filter = ['is_entry', 'timestamp']
    search_fields = ['employee__username']
    date_hierarchy = 'timestamp'

@admin.register(WorkConfiguration)
class WorkConfigurationAdmin(admin.ModelAdmin):
    list_display = ['user', 'hours_per_day', 'hourly_rate', 'cutoff_type', 'bonus']
    list_filter = ['cutoff_type']
    search_fields = ['user__username']

@admin.register(DailyWorkSummary)
class DailyWorkSummaryAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'time_in', 'time_out', 'total_hours', 'late_minutes', 'net_pay']
    list_filter = ['date']
    search_fields = ['employee__username']
    date_hierarchy = 'date'
    readonly_fields = ['late_deduction_minutes', 'gross_pay', 'deductions', 'net_pay']

@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(admin.ModelAdmin):
    list_display = ['employee', 'period_type', 'start_date', 'end_date', 'total_hours', 'net_pay', 'is_finalized']
    list_filter = ['period_type', 'is_finalized', 'start_date']
    search_fields = ['employee__username']
    readonly_fields = ['total_hours', 'total_gross_pay', 'total_deductions', 'net_pay']