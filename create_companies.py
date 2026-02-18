"""Create company and package data on PythonAnywhere"""
import requests
import time

API_TOKEN = "a0a783bc25a51c6cb5c0e9dc42298c6b18165495"
USERNAME = "rohaannoor123"
BASE_URL = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}
DOMAIN = f"{USERNAME}.pythonanywhere.com"

script = r'''#!/usr/bin/env python
"""Create companies and tour packages"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'touripk.settings')
sys.path.insert(0, '/home/rohaannoor123/touripk/pkk')
django.setup()

from packages.models import Company, Package
from users.models import CustomUser
from django.utils import timezone
from django.utils.text import slugify
from datetime import date, timedelta

admin = CustomUser.objects.filter(is_superuser=True).first()
if not admin:
    admin = CustomUser.objects.create_superuser('admin', 'admin@touripk.com', 'admin123456')
    print(f"Created admin: {admin.username}")

# Create Companies
companies_data = [
    {
        "name": "Northern Ways Tours",
        "slug": "northern-ways-tours",
        "description": "Northern Ways Tours is a premier travel company specializing in tours to the breathtaking northern areas of Pakistan. With over 10 years of experience, we offer unforgettable journeys through Hunza, Skardu, Fairy Meadows, and more.",
        "logo": "companies/nothernways.jpg",
        "email": "info@northernways.pk",
        "phone": "+92-321-1234567",
        "address": "Office 12, Blue Area, Islamabad",
        "website": "https://northernways.pk",
        "rating": 4.8,
        "approval_status": "approved",
        "is_active": True,
    },
    {
        "name": "Smile Miles Travel",
        "slug": "smile-miles-travel",
        "description": "Smile Miles Travel brings joy to every journey. We specialize in family-friendly tours, honeymoon packages, and adventure trips across Pakistan. Customer satisfaction is our top priority.",
        "logo": "companies/smile_miles.jpg",
        "email": "contact@smilemiles.pk",
        "phone": "+92-333-9876543",
        "address": "Shop 5, F-7 Markaz, Islamabad",
        "website": "https://smilemiles.pk",
        "rating": 4.6,
        "approval_status": "approved",
        "is_active": True,
    },
    {
        "name": "TouriPK Adventures",
        "slug": "touripk-adventures",
        "description": "TouriPK Adventures is your gateway to exploring Pakistan like never before. From the peaks of K2 to the beaches of Gwadar, we cover it all with premium service and competitive pricing.",
        "logo": "Logos/touri.png",
        "email": "tours@touripk.com",
        "phone": "+92-300-5551234",
        "address": "Mall Road, Murree",
        "website": "https://touripk.com",
        "rating": 4.9,
        "approval_status": "approved",
        "is_active": True,
    },
    {
        "name": "Pakistan Explorers",
        "slug": "pakistan-explorers",
        "description": "Pakistan Explorers has been taking adventurers to the most remote and beautiful corners of Pakistan since 2015. Our expert guides and well-planned itineraries ensure a safe and memorable experience.",
        "logo": "",
        "email": "explore@pakexplorers.pk",
        "phone": "+92-312-7778899",
        "address": "GT Road, Rawalpindi",
        "website": "",
        "rating": 4.5,
        "approval_status": "approved",
        "is_active": True,
    },
    {
        "name": "Mountain Breeze Tours",
        "slug": "mountain-breeze-tours",
        "description": "Mountain Breeze Tours offers luxury and budget-friendly tours to Northern Pakistan. Specializing in Gilgit-Baltistan and Chitral regions with comfortable transport and quality accommodations.",
        "logo": "",
        "email": "info@mountainbreeze.pk",
        "phone": "+92-345-1112233",
        "address": "Karakoram Highway, Gilgit",
        "website": "",
        "rating": 4.3,
        "approval_status": "approved",
        "is_active": True,
    },
]

for data in companies_data:
    logo_val = data.pop("logo")
    company, created = Company.objects.get_or_create(
        slug=data['slug'],
        defaults={**data, 'owner': admin, 'approved_at': timezone.now()}
    )
    if created and logo_val:
        company.logo = logo_val
        company.save()
        print(f"  Created company: {company.name}")
    elif created:
        print(f"  Created company: {company.name} (no logo)")
    else:
        # Update existing
        company.approval_status = 'approved'
        company.is_active = True
        company.approved_at = timezone.now()
        company.save()
        print(f"  Updated company: {company.name}")

# Create Packages
packages_data = [
    {
        "company_slug": "northern-ways-tours",
        "name": "Hunza Valley Explorer - 5 Days",
        "slug": "hunza-valley-explorer-5-days",
        "description": "Experience the magical Hunza Valley with visits to Baltit Fort, Eagle's Nest viewpoint, Attabad Lake, and Passu Cones. Includes comfortable hotel stays and all meals.",
        "package_type": "adventure",
        "destination_names": "Hunza Valley, Karimabad, Passu, Attabad Lake",
        "duration_days": 5,
        "duration_nights": 4,
        "price_per_person": 35000,
        "child_price": 20000,
        "inclusions": "Transport from Islamabad\nHotel accommodation (4 nights)\nAll meals (breakfast, lunch, dinner)\nProfessional guide\nSightseeing tours\nEntry tickets",
        "exclusions": "Personal expenses\nTravel insurance\nTips for guide",
        "itinerary": "Day 1: Islamabad to Chilas\nDay 2: Chilas to Hunza - Attabad Lake visit\nDay 3: Hunza Valley sightseeing - Baltit Fort, Eagle's Nest\nDay 4: Passu Cones and Borith Lake\nDay 5: Return to Islamabad",
        "image": "packages/hunza-valley-5-days.jpg",
        "min_people": 4,
        "max_people": 15,
        "is_featured": True,
    },
    {
        "company_slug": "northern-ways-tours",
        "name": "Fairy Meadows Trek - 5 Days",
        "slug": "fairy-meadows-trek-5-days",
        "description": "Trek to the stunning Fairy Meadows with breathtaking views of Nanga Parbat. Perfect for adventure seekers looking for an unforgettable mountain experience.",
        "package_type": "adventure",
        "destination_names": "Fairy Meadows, Nanga Parbat Base Camp",
        "duration_days": 5,
        "duration_nights": 4,
        "price_per_person": 42000,
        "child_price": 25000,
        "inclusions": "Transport from Islamabad\nCamping gear\nAll meals\nProfessional trekking guide\nPorters",
        "exclusions": "Personal trekking gear\nTravel insurance",
        "itinerary": "Day 1: Islamabad to Raikot Bridge\nDay 2: Jeep ride to Tato, trek to Fairy Meadows\nDay 3: Explore Fairy Meadows, hike to Nanga Parbat viewpoint\nDay 4: Trek to Beyal Camp\nDay 5: Return to Islamabad",
        "image": "packages/fairy-meadows-5-days.jpg",
        "min_people": 4,
        "max_people": 12,
        "is_featured": True,
    },
    {
        "company_slug": "smile-miles-travel",
        "name": "Swat Kalam Family Tour - 3 Days",
        "slug": "swat-kalam-family-tour-3-days",
        "description": "A perfect family getaway to the Switzerland of Pakistan. Visit Mingora, Malam Jabba, Kalam Valley, and Mahodand Lake.",
        "package_type": "family",
        "destination_names": "Swat Valley, Kalam, Malam Jabba, Mahodand Lake",
        "duration_days": 3,
        "duration_nights": 2,
        "price_per_person": 18000,
        "child_price": 10000,
        "inclusions": "AC Transport\nHotel (2 nights)\nBreakfast and dinner\nSightseeing",
        "exclusions": "Lunch\nPersonal expenses\nEntry tickets",
        "itinerary": "Day 1: Islamabad to Swat - Malam Jabba visit\nDay 2: Kalam Valley and Mahodand Lake\nDay 3: Return to Islamabad via Mingora",
        "image": "packages/swat-kalam-3-days.jpg",
        "min_people": 2,
        "max_people": 20,
        "is_featured": True,
    },
    {
        "company_slug": "smile-miles-travel",
        "name": "Naran Kaghan Adventure - 3 Days",
        "slug": "naran-kaghan-adventure-3-days",
        "description": "Explore the stunning Naran Kaghan valley with visits to Lake Saif-ul-Malook, Lulusar Lake, and Babusar Top.",
        "package_type": "adventure",
        "destination_names": "Naran, Kaghan Valley, Lake Saif-ul-Malook, Babusar Top",
        "duration_days": 3,
        "duration_nights": 2,
        "price_per_person": 15000,
        "child_price": 8000,
        "inclusions": "Transport\nHotel (2 nights)\nBreakfast\nGuide",
        "exclusions": "Jeep ride to Saif-ul-Malook\nLunch and dinner\nPersonal expenses",
        "itinerary": "Day 1: Islamabad to Naran\nDay 2: Lake Saif-ul-Malook and Lulusar Lake\nDay 3: Babusar Top and return",
        "image": "packages/naran-valley-3-days.jpg",
        "min_people": 4,
        "max_people": 25,
        "is_featured": True,
    },
    {
        "company_slug": "touripk-adventures",
        "name": "Neelum Valley Escape - 3 Days",
        "slug": "neelum-valley-escape-3-days",
        "description": "Discover the pristine beauty of Neelum Valley in Azad Kashmir. Crystal clear rivers, lush green forests, and stunning waterfalls await you.",
        "package_type": "family",
        "destination_names": "Neelum Valley, Keran, Sharda, Kel",
        "duration_days": 3,
        "duration_nights": 2,
        "price_per_person": 20000,
        "child_price": 12000,
        "inclusions": "Transport\nHotel accommodation\nAll meals\nGuide\nEntry permits",
        "exclusions": "Personal expenses\nAdditional activities",
        "itinerary": "Day 1: Islamabad to Muzaffarabad to Keran\nDay 2: Sharda Fort and Kel exploration\nDay 3: Return to Islamabad",
        "image": "packages/neelum-valley-3-days.jpg",
        "min_people": 2,
        "max_people": 15,
        "is_featured": True,
    },
    {
        "company_slug": "touripk-adventures",
        "name": "Kashmir Arang Kel Trek - 3 Days",
        "slug": "kashmir-arang-kel-trek-3-days",
        "description": "Trek to the paradise on earth - Arang Kel in Azad Kashmir. A chairlift ride over the lush valley followed by a scenic trek makes this an unforgettable adventure.",
        "package_type": "adventure",
        "destination_names": "Azad Kashmir, Kel, Arang Kel",
        "duration_days": 3,
        "duration_nights": 2,
        "price_per_person": 22000,
        "child_price": 14000,
        "inclusions": "Transport from Islamabad\nWooden hut stay\nAll meals\nGuide\nChairlift ticket",
        "exclusions": "Personal gear\nTravel insurance",
        "itinerary": "Day 1: Islamabad to Kel\nDay 2: Chairlift to Arang Kel, exploration\nDay 3: Return to Islamabad",
        "image": "packages/kashmir-arang-kel-3-days-northway.jpg",
        "min_people": 4,
        "max_people": 12,
        "is_featured": True,
    },
    {
        "company_slug": "pakistan-explorers",
        "name": "Hunza Naltar Valley - 5 Days",
        "slug": "hunza-naltar-valley-5-days",
        "description": "Combine the beauty of Hunza with the colorful Naltar Lakes. Visit Karimabad, Altit Fort, and the mesmerizing blue and green lakes of Naltar Valley.",
        "package_type": "luxury",
        "destination_names": "Hunza Valley, Naltar Valley, Karimabad",
        "duration_days": 5,
        "duration_nights": 4,
        "price_per_person": 45000,
        "child_price": 28000,
        "inclusions": "Luxury transport\nPremium hotel stays\nAll meals\nPrivate guide\nAll entry tickets\nJeep to Naltar",
        "exclusions": "Shopping\nPersonal expenses\nTravel insurance",
        "itinerary": "Day 1: Fly to Gilgit\nDay 2: Naltar Valley and Lakes\nDay 3: Karimabad sightseeing\nDay 4: Attabad Lake and Passu\nDay 5: Return flight to Islamabad",
        "image": "packages/hunza-naltar-valley-5-days-northway.jpg",
        "min_people": 2,
        "max_people": 10,
        "is_featured": True,
    },
    {
        "company_slug": "mountain-breeze-tours",
        "name": "Kalam Malam Jabba Tour - 3 Days",
        "slug": "kalam-malam-jabba-tour-3-days",
        "description": "Enjoy skiing at Malam Jabba and the serene beauty of Kalam Valley. Perfect winter and summer getaway for families and groups.",
        "package_type": "family",
        "destination_names": "Kalam, Malam Jabba, Swat Valley",
        "duration_days": 3,
        "duration_nights": 2,
        "price_per_person": 16000,
        "child_price": 9000,
        "inclusions": "AC Coaster transport\nHotel (2 nights)\nBreakfast and dinner\nSightseeing",
        "exclusions": "Skiing charges\nLunch\nPersonal expenses",
        "itinerary": "Day 1: Islamabad to Malam Jabba\nDay 2: Kalam Valley exploration\nDay 3: Return to Islamabad",
        "image": "packages/kalam-malam-jabba-3-days-northway.jpg",
        "min_people": 6,
        "max_people": 30,
        "is_featured": True,
    },
]

for pkg_data in packages_data:
    company_slug = pkg_data.pop("company_slug")
    try:
        company = Company.objects.get(slug=company_slug)
    except Company.DoesNotExist:
        print(f"  SKIP: Company {company_slug} not found")
        continue
    
    image_val = pkg_data.pop("image", "")
    pkg, created = Package.objects.get_or_create(
        slug=pkg_data['slug'],
        defaults={
            **pkg_data,
            'company': company,
            'is_active': True,
            'is_approved': True,
            'available_from': date.today(),
            'available_to': date.today() + timedelta(days=365),
        }
    )
    if created and image_val:
        pkg.image = image_val
        pkg.save()
        print(f"  Created package: {pkg.name} ({company.name})")
    elif created:
        print(f"  Created package: {pkg.name} (no image)")
    else:
        pkg.is_active = True
        pkg.is_approved = True
        pkg.save()
        print(f"  Updated package: {pkg.name}")

print(f"\n=== FINAL STATUS ===")
print(f"Companies: {Company.objects.count()} total, {Company.objects.filter(is_active=True, approval_status='approved').count()} active & approved")
print(f"Packages: {Package.objects.count()} total, {Package.objects.filter(is_active=True, is_approved=True).count()} active & approved")
print(f"\nCompany list:")
for c in Company.objects.all():
    print(f"  [{c.pk}] {c.name} - status={c.approval_status}, active={c.is_active}, logo={c.logo}")
    pkgs = Package.objects.filter(company=c)
    for p in pkgs:
        print(f"      - {p.name} (Rs.{p.price_per_person}/person)")
print("\nALL DONE!")
'''

# Upload script
remote_path = f"/home/{USERNAME}/create_companies.py"
url = f"{BASE_URL}/files/path{remote_path}"
resp = requests.post(url, headers=HEADERS, files={"content": ("create_companies.py", script.encode(), "text/plain")})
print(f"Script uploaded: {resp.status_code}")

# Run via console
print("\n=== RUNNING ===")
consoles_url = f"{BASE_URL}/consoles/"
resp = requests.get(consoles_url, headers=HEADERS)
consoles = resp.json() if resp.status_code == 200 else []

bash_console = None
for c in consoles:
    if 'bash' in c.get('executable', '').lower():
        bash_console = c['id']
        break

if not bash_console:
    resp = requests.post(consoles_url, headers=HEADERS, json={
        "executable": "bash",
        "working_directory": f"/home/{USERNAME}/touripk/pkk"
    })
    if resp.status_code in (200, 201):
        bash_console = resp.json()['id']
        time.sleep(3)

print(f"  Console: {bash_console}")

send_url = f"{BASE_URL}/consoles/{bash_console}/send_input/"
cmd = "cd /home/rohaannoor123/touripk/pkk && source /home/rohaannoor123/.virtualenvs/touripk-venv/bin/activate && python /home/rohaannoor123/create_companies.py 2>&1\n"
resp = requests.post(send_url, headers=HEADERS, json={"input": cmd})
print(f"  Sent: {resp.status_code}")

print("  Waiting for execution...")
time.sleep(15)

output_url = f"{BASE_URL}/consoles/{bash_console}/get_latest_output/"
resp = requests.get(output_url, headers=HEADERS)
if resp.status_code == 200:
    output = resp.json().get('output', '')
    print(f"\n{output[-5000:]}")

# Reload
print("\n=== RELOADING ===")
url = f"{BASE_URL}/webapps/{DOMAIN}/reload/"
resp = requests.post(url, headers=HEADERS)
print(f"  Reload: {resp.status_code}")
time.sleep(5)

# Verify
resp = requests.get(f"https://{DOMAIN}/", timeout=15)
print(f"\n  Home: {resp.status_code} ({len(resp.content)} bytes)")
if 'Northern Ways' in resp.text or 'Smile Miles' in resp.text or 'TouriPK' in resp.text:
    print("  SUCCESS: Companies are showing on homepage!")
else:
    print("  Companies may not be visible yet")

if 'No Featured' in resp.text:
    print("  WARNING: No Featured Destinations")
else:
    print("  OK: Destinations showing")
