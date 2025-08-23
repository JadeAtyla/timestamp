Setting up a Django project with a MySQL database and secure credentials involves several steps. Here's a guide to get you started on your timestamp management system.

## 1\. Project Setup and Virtual Environment

First, ensure your project structure is ready. You should have already created your project and app.

```bash
# Activate your virtual environment
cd timestamp
python manage.py startapp core
```

## 2\. Install Dependencies

You'll need `mysqlclient` to connect Django to MySQL, `mysql-connector-python` as a backup, and `python-dotenv` for managing environment variables.

```bash
pip install mysqlclient mysql-connector-python python-dotenv
```

## 3\. Configure `.env` for Secure Credentials

Create a `.env` file in your project's root directory (same level as `manage.py`). This file will store your sensitive information. **Do not commit this file to your version control system.** Add `.env` to your `.gitignore` file.

```ini
# .env
SECRET_KEY=your_very_secret_key_here
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=3306
```

## 4\. Configure `settings.py`

Modify your `settings.py` file to read from the `.env` file and use the MySQL database.

```python
# timestamp/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}
```

## 5\. Database Setup

Before you can run migrations, you need to create the database in MySQL. Use your preferred MySQL client (e.g., MySQL Workbench, command-line) to create a database with the name you specified in your `.env` file.

```sql
CREATE DATABASE your_database_name;
```

Then, run Django migrations to create the necessary tables.

```bash
python manage.py makemigrations
python manage.py migrate
```

## 6\. Model and User Management

You'll need to define models for your `Employee` and `Timestamp` records. You can use Django's built-in `User` model and extend it for roles using a `ForeignKey`.

```python
# core/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('employee', 'Employee'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='employee')

class Timestamp(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_entry = models.BooleanField(default=True) # True for login, False for logout
```

## 7\. Views and Logic

You'll need two sets of views: one for employees and one for the admin. Use `@login_required` and a custom decorator to enforce role-based access.

### Employee View Logic

  * **Face Recognition:** This is an advanced topic. You would use a library like **OpenCV** and a face recognition model (e.g., `face_recognition` library) to handle this. The view would capture a user's face, compare it to a stored face encoding, and if it matches, create a `Timestamp` record.
  * **Timestamp Logging:** The view would check the last timestamp for the logged-in user to determine if the new entry should be a login or logout.

### Admin View Logic

  * **Dashboard:** This view will display all employee and timestamp data in a table.
  * **Add/Edit/Delete Records:** This will be handled by a form view. To ensure security, you'll need to create a form that requires the admin to re-enter their password before the changes are saved. You can use a form field for the password and a custom `clean_password` method to validate it against the current admin user's password.

## 8\. URL Configuration and Templates

Set up your URLs to point to your new views and create corresponding HTML templates for the employee and admin dashboards. Use Django's template language to display data and forms.