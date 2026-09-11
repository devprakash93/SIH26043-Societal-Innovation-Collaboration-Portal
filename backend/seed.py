import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import User

# Ensure Admin exists
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@samadhanx.com', 'Demo@1234', role='gov_admin')
    print("Demo Admin user created successfully!")
else:
    print("Demo Admin already exists.")

# Ensure Citizen exists
if not User.objects.filter(username='citizen1').exists():
    User.objects.create_user('citizen1', 'citizen1@samadhanx.com', 'Demo@1234', role='citizen')
    print("Demo Citizen created.")
