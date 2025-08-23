from django.db import models
from django.contrib.auth.models import User

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

class Timestamp(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_entry = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.employee.username} - {'Entry' if self.is_entry else 'Exit'} at {self.timestamp}"