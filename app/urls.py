from django.urls import path
from . import views

urlpatterns = [
    # Main authentication and dashboard views
    path('', views.landing_page, name='landing_page'),
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('employee/', views.employee_dashboard, name='employee_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Password management
    path('change-password/', views.change_password, name='change_password'),
    path('user/reset-password/<int:user_id>/', views.admin_reset_password, name='admin_reset_password'),
    path('user/<int:user_id>/', views.user_detail, name='user_detail'),
    
    # Work configuration and payroll management
    path('user/work-config/<int:user_id>/', views.edit_work_config, name='edit_work_config'),
    path('user/payroll/<int:user_id>/', views.user_payroll, name='user_payroll'),
    path('user/generate-payroll/<int:user_id>/', views.generate_payroll, name='generate_payroll'),
    
    # API endpoints for the frontend
    path('api/logs/', views.api_get_logs, name='api_get_logs'),
    path('api/timestamp/', views.api_create_timestamp, name='api_create_timestamp'),
    path('api/payroll-summary/', views.api_get_payroll_summary, name='api_get_payroll_summary'),
]