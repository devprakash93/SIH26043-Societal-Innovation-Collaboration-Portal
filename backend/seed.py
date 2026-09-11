import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import User
from master_data.models import District
from universities.models import University
from industry.models import IndustryPartner

# 1. Gov Admin
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@samadhanx.com', 'Demo@1234', role='gov_admin')
    print("Demo Admin created.")

# 2. Citizen
if not User.objects.filter(username='citizen1').exists():
    User.objects.create_user('citizen1', 'citizen1@samadhanx.com', 'Demo@1234', role='citizen')
    print("Demo Citizen created.")

# 3. HEI SPOC (needs District & University)
if not User.objects.filter(username='hei_spoc1').exists():
    spoc = User.objects.create_user('hei_spoc1', 'hei@samadhanx.com', 'Demo@1234', role='hei_spoc')
    district, _ = District.objects.get_or_create(name='Demo District')
    University.objects.create(
        name='Demo University',
        district=district,
        spoc=spoc,
        status='APPROVED'
    )
    print("Demo HEI SPOC created.")

# 4. Faculty Mentor
if not User.objects.filter(username='faculty1').exists():
    User.objects.create_user('faculty1', 'faculty@samadhanx.com', 'Demo@1234', role='faculty_mentor')
    print("Demo Faculty created.")

# 5. Industry Partner (needs IndustryPartner model)
if not User.objects.filter(username='industry1').exists():
    ind_user = User.objects.create_user('industry1', 'industry@samadhanx.com', 'Demo@1234', role='industry_partner')
    IndustryPartner.objects.create(
        user=ind_user,
        company_name='Demo Corp',
        registration_number='DEMO123',
        status='APPROVED',
        sector='Technology'
    )
    print("Demo Industry Partner created.")

print("All Demo Data Seeded Successfully!")
