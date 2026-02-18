"""Create destination and product data directly via Django ORM on PythonAnywhere"""
import requests
import time

API_TOKEN = "a0a783bc25a51c6cb5c0e9dc42298c6b18165495"
USERNAME = "rohaannoor123"
BASE_URL = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}
DOMAIN = f"{USERNAME}.pythonanywhere.com"

def upload_and_run():
    # Script that creates data directly using Django ORM
    script = r'''#!/usr/bin/env python
"""Create destination and product data directly"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'touripk.settings')
sys.path.insert(0, '/home/rohaannoor123/touripk/pkk')
django.setup()

from content.models import Destination, Product, CostComponent
from django.utils import timezone

print("=== DEBUGGING LOADDATA ===")
# First try to understand why loaddata failed
from django.core.management import call_command
from io import StringIO
out = StringIO()
err = StringIO()
try:
    call_command('loaddata', 'content/fixtures/initial_data.json', verbosity=2, stdout=out, stderr=err)
    print(f"loaddata stdout: {out.getvalue()}")
    print(f"loaddata stderr: {err.getvalue()}")
except Exception as e:
    print(f"loaddata ERROR: {e}")
    print(f"stdout so far: {out.getvalue()}")
    print(f"stderr so far: {err.getvalue()}")

# Check again
print(f"\nAfter loaddata: {Destination.objects.count()} destinations, {Product.objects.count()} products")

# If loaddata still didn't work, create data manually
if Destination.objects.count() == 0:
    print("\n=== CREATING DATA MANUALLY ===")
    destinations_data = [
        {"name": "Hunza Valley", "description": "Hunza Valley is a mountainous valley in the Gilgit-Baltistan region of Pakistan. The valley is situated at an elevation of 2,438 meters, surrounded by snow-capped peaks including Rakaposhi, Ultar Sar, and Ladyfinger Peak.", "image": "destinations/hunza-valley.jpg", "city": "Karimabad"},
        {"name": "Fairy Meadows", "description": "Fairy Meadows, named by German climbers and locally known as Joot, is a grassland near Nanga Parbat base camp. Its spectacular beauty and accessibility make it one of the most popular tourist destinations in Pakistan.", "image": "destinations/fairy-meadows.jpg", "city": "Chilas"},
        {"name": "Faisal Mosque", "description": "The Faisal Mosque is the national mosque of Pakistan, located in the capital city Islamabad. It is one of the largest mosques in the world and an iconic symbol of Pakistani architecture.", "image": "destinations/faisal-mosque.jpg", "city": "Islamabad"},
        {"name": "Badshahi Mosque", "description": "The Badshahi Mosque in Lahore is one of the most iconic landmarks of Pakistan, built in 1673 during the Mughal era. It is the second largest mosque in Pakistan and a masterpiece of Mughal architecture.", "image": "destinations/badshahi-mosque.jpg", "city": "Lahore"},
        {"name": "Baltit Fort", "description": "The Baltit Fort in Hunza is an ancient fort dating back 700 years. Restored by the Aga Khan Trust for Culture, it is a remarkable example of local architecture and offers stunning views of the Hunza Valley.", "image": "destinations/baltit-fort.jpg", "city": "Karimabad"},
        {"name": "Deosai Plains", "description": "Known as the Land of Giants, Deosai Plains is the second highest plateau in the world. Located in Gilgit-Baltistan, it is a biodiversity hotspot and home to unique wildlife including the Himalayan brown bear.", "image": "destinations/deosai-plains.jpg", "city": "Skardu"},
        {"name": "K2 Base Camp", "description": "K2, the second highest mountain in the world, is accessible via the famous Concordia trek from Skardu. The base camp trek is one of the most iconic adventures in the world.", "image": "destinations/k2-basecamp.jpg", "city": "Skardu"},
        {"name": "Swat Valley", "description": "Known as the Switzerland of Pakistan, Swat Valley features lush green meadows, snow-covered mountains, gushing rivers and waterfalls, and rich archaeological sites.", "image": "destinations/swat-valley.jpg", "city": "Mingora"},
        {"name": "Kalash Valley", "description": "The Kalash valleys are home to the unique Kalash people with their distinct culture, festivals, and traditions. The valleys of Bumburet, Rumbur, and Birir offer an unmatched cultural experience.", "image": "destinations/kalash-valley.jpg", "city": "Chitral"},
        {"name": "Naltar Valley", "description": "Naltar Valley is known for its colorful lakes and pine forests. The Naltar Lakes, with their unique blue and green colors, are among the most beautiful lakes in Pakistan.", "image": "destinations/naltar-valley.jpg", "city": "Gilgit"},
        {"name": "Shalimar Gardens", "description": "The Shalimar Gardens in Lahore are a stunning example of Mughal garden design, built by Emperor Shah Jahan in 1641. A UNESCO World Heritage Site.", "image": "destinations/shalimar-gardens.jpg", "city": "Lahore"},
        {"name": "Tomb of Jahangir", "description": "The Tomb of Emperor Jahangir, built in 1637, is a masterpiece of Mughal architecture located in Shahdara, Lahore. It features beautiful pietra dura and fresco work.", "image": "destinations/tomb-jahangir.jpg", "city": "Lahore"},
        {"name": "Mohenjo-Daro", "description": "Mohenjo-daro is an archaeological site in Sindh, built around 2500 BCE. It is one of the largest settlements of the ancient Indus Valley Civilisation and a UNESCO World Heritage Site.", "image": "destinations/mohenjo-daro.jpg", "city": "Larkana"},
        {"name": "Passu Cones", "description": "The Passu Cones are a group of pointed mountain peaks near Passu village in Hunza. These dramatic peaks and the famous Passu Suspension Bridge attract visitors from around the world.", "image": "destinations/passu-cones.jpg", "city": "Passu"},
        {"name": "Lahore Fort", "description": "Lahore Fort is a citadel in the city of Lahore. The fortress is located at the northern end of Lahore's Walled City and spreads over an area greater than 20 hectares. A UNESCO World Heritage Site.", "image": "destinations/lahore-fort.jpg", "city": "Lahore"},
    ]
    
    for data in destinations_data:
        d, created = Destination.objects.get_or_create(
            name=data['name'],
            defaults={
                'description': data['description'],
                'image': data['image'],
                'city': data['city'],
                'is_featured': True,
                'is_active': True,
                'country': 'Pakistan',
            }
        )
        if created:
            print(f"  Created: {d.name}")
        else:
            d.is_featured = True
            d.is_active = True
            d.save()
            print(f"  Updated: {d.name}")

if Product.objects.count() == 0:
    products_data = [
        {"name": "Hunza Dried Apricots", "description": "Organic dried apricots from the Hunza Valley, known for their exceptional taste and nutritional value.", "price": 599.99, "image": "products/dried-apricots.jpg"},
        {"name": "Gilgit Walnuts", "description": "Premium quality walnuts from the valleys of Gilgit-Baltistan, hand-picked and naturally dried.", "price": 899.99, "image": "products/Walnuts.jpg"},
        {"name": "Mountain Shilajit", "description": "Pure Himalayan Shilajit from the mountains of Northern Pakistan, a natural health supplement.", "price": 2499.99, "image": "products/Shilajit.jpg"},
        {"name": "Hunza Almonds", "description": "Fresh organic almonds from Hunza Valley, known for their rich flavor and health benefits.", "price": 1299.99, "image": "products/Almond.jpg"},
    ]
    
    for data in products_data:
        p, created = Product.objects.get_or_create(
            name=data['name'],
            defaults={
                'description': data['description'],
                'price': data['price'],
                'image': data['image'],
                'is_active': True,
                'is_approved': True,
                'is_featured': True,
            }
        )
        if created:
            print(f"  Created product: {p.name}")
        else:
            p.is_active = True
            p.is_approved = True 
            p.save()
            print(f"  Updated product: {p.name}")

# Create cost components
if CostComponent.objects.count() == 0:
    dest_ids = list(Destination.objects.values_list('id', flat=True)[:2])
    if dest_ids:
        first_dest = Destination.objects.get(pk=dest_ids[0])
        costs = [
            {"name": "Basic Camping", "category": "camping", "base_cost": 2000, "unit": "per night", "description": "Basic camping setup with tent"},
            {"name": "Deluxe Camping", "category": "camping", "base_cost": 5000, "unit": "per night", "description": "Luxury camping with amenities"},
            {"name": "Private Car Transfer", "category": "transport", "base_cost": 8000, "unit": "per trip", "description": "Round trip private car transfer"},
            {"name": "Standard Meals", "category": "food", "base_cost": 1500, "unit": "per person per day", "description": "Three meals at local restaurants"},
            {"name": "Guided Tour", "category": "activities", "base_cost": 4000, "unit": "per person", "description": "Full day guided tour with lunch"},
            {"name": "Local Crafts", "category": "shopping", "base_cost": 5000, "unit": "per package", "description": "Selection of local handicrafts"},
        ]
        for c in costs:
            CostComponent.objects.create(destination=first_dest, **c)
        print(f"\n  Created {len(costs)} cost components for {first_dest.name}")

# Also make sure superuser exists
from users.models import CustomUser
if not CustomUser.objects.filter(username='admin').exists():
    u = CustomUser.objects.create_superuser('admin', 'admin@touripk.com', 'admin123456')
    print(f"\nCreated superuser: {u.username}")
else:
    print(f"\nSuperuser 'admin' already exists")

# Make sure admin has is_staff and is_superuser
admin_user = CustomUser.objects.get(username='admin')
admin_user.is_staff = True
admin_user.is_superuser = True
admin_user.is_active = True
admin_user.save()
print(f"Admin user verified: is_staff={admin_user.is_staff}, is_superuser={admin_user.is_superuser}")

print(f"\n=== FINAL STATUS ===")
print(f"Destinations: {Destination.objects.count()} total, {Destination.objects.filter(is_featured=True).count()} featured, {Destination.objects.filter(is_active=True).count()} active")
print(f"Products: {Product.objects.count()} total")
print(f"Cost Components: {CostComponent.objects.count()} total")
print(f"Users: {CustomUser.objects.count()} total, {CustomUser.objects.filter(is_superuser=True).count()} superusers")
print("\nALL DONE!")
'''

    # Upload script
    remote_path = f"/home/{USERNAME}/create_data.py"
    url = f"{BASE_URL}/files/path{remote_path}"
    resp = requests.post(url, headers=HEADERS, files={"content": ("create_data.py", script.encode(), "text/plain")})
    print(f"Script uploaded: {resp.status_code}")
    
    # Run via console
    print("\n=== RUNNING CREATE DATA SCRIPT ===")
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
    cmd = "cd /home/rohaannoor123/touripk/pkk && source /home/rohaannoor123/.virtualenvs/touripk-venv/bin/activate && python /home/rohaannoor123/create_data.py 2>&1\n"
    resp = requests.post(send_url, headers=HEADERS, json={"input": cmd})
    print(f"  Sent: {resp.status_code}")
    
    # Wait longer for execution
    print("  Waiting for execution...")
    time.sleep(15)
    
    # Get output
    output_url = f"{BASE_URL}/consoles/{bash_console}/get_latest_output/"
    resp = requests.get(output_url, headers=HEADERS)
    if resp.status_code == 200:
        output = resp.json().get('output', '')
        print(f"\n{output[-4000:]}")
    
    return True

def reload_verify():
    print("\n=== RELOADING ===")
    url = f"{BASE_URL}/webapps/{DOMAIN}/reload/"
    resp = requests.post(url, headers=HEADERS)
    print(f"  Reload: {resp.status_code}")
    time.sleep(5)
    
    resp = requests.get(f"https://{DOMAIN}/", timeout=15)
    print(f"\n  Home: {resp.status_code} ({len(resp.content)} bytes)")
    
    if 'No Featured' in resp.text:
        print("  STILL showing 'No Featured Destinations'")
    else:
        print("  FIXED! Destinations are now showing on homepage!")
    
    # Check a specific destination page
    resp2 = requests.get(f"https://{DOMAIN}/destinations/", timeout=15)
    print(f"  Destinations page: {resp2.status_code} ({len(resp2.content)} bytes)")
    
    resp3 = requests.get(f"https://{DOMAIN}/media/destinations/hunza-valley.jpg", timeout=15)
    print(f"  Media test: {resp3.status_code}")

if __name__ == "__main__":
    upload_and_run()
    reload_verify()
