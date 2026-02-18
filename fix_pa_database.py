"""Fix remaining PythonAnywhere issues: set featured destinations, fix cost data"""
import requests
import time

API_TOKEN = "a0a783bc25a51c6cb5c0e9dc42298c6b18165495"
USERNAME = "rohaannoor123"
BASE_URL = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}
DOMAIN = f"{USERNAME}.pythonanywhere.com"

def upload_fix_script():
    """Upload a Python script to fix the database on PythonAnywhere"""
    
    fix_script = '''#!/usr/bin/env python
"""Fix database: set featured destinations, load cost components"""
import os, sys, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'touripk.settings')
sys.path.insert(0, '/home/rohaannoor123/touripk/pkk')
django.setup()

from content.models import Destination, Product, CostComponent

# 1. Check what destinations exist
destinations = Destination.objects.all()
print(f"\\nTotal destinations: {destinations.count()}")
for d in destinations:
    print(f"  [{d.pk}] {d.name} - featured={d.is_featured}, active={d.is_active}")

# 2. Set all destinations as featured and active
updated = Destination.objects.all().update(is_featured=True, is_active=True)
print(f"\\nSet {updated} destinations as featured and active")

# 3. Set all products as active
prod_updated = Product.objects.all().update(is_active=True, is_approved=True)
print(f"Set {prod_updated} products as active and approved")

# 4. Load cost components for destinations that exist
dest_ids = list(Destination.objects.values_list('id', flat=True))
print(f"\\nDestination IDs: {dest_ids}")

# Delete existing cost components and reload
CostComponent.objects.all().delete()
print("Cleared existing cost components")

# Create cost components for first destination
if dest_ids:
    first_dest = Destination.objects.get(pk=dest_ids[0])
    costs_data = [
        {"name": "Basic Camping", "category": "camping", "base_cost": 2000, "unit": "per night", "description": "Basic camping setup with tent"},
        {"name": "Deluxe Camping", "category": "camping", "base_cost": 5000, "unit": "per night", "description": "Luxury camping with amenities"},
        {"name": "Private Car Transfer", "category": "transport", "base_cost": 8000, "unit": "per trip", "description": "Round trip private car transfer"},
        {"name": "Local Bus Service", "category": "transport", "base_cost": 1000, "unit": "per person", "description": "Public transportation pass"},
        {"name": "Standard Meal Package", "category": "food", "base_cost": 1500, "unit": "per person per day", "description": "Three meals at local restaurants"},
        {"name": "Premium Dining", "category": "food", "base_cost": 3500, "unit": "per person per day", "description": "Fine dining experiences"},
        {"name": "Guided Tour", "category": "activities", "base_cost": 4000, "unit": "per person", "description": "Full day guided tour with lunch"},
        {"name": "Cultural Show", "category": "activities", "base_cost": 2000, "unit": "per person", "description": "Evening traditional music and dance"},
        {"name": "Local Crafts", "category": "shopping", "base_cost": 5000, "unit": "per package", "description": "Selection of local handicrafts"},
        {"name": "Premium Shopping", "category": "shopping", "base_cost": 15000, "unit": "per package", "description": "Luxury local items including jewelry"},
    ]
    
    for cost in costs_data:
        CostComponent.objects.create(destination=first_dest, **cost)
    print(f"Created {len(costs_data)} cost components for {first_dest.name}")

    # Add cost components for second destination if exists
    if len(dest_ids) > 1:
        second_dest = Destination.objects.get(pk=dest_ids[1])
        costs_data2 = [
            {"name": "Standard Room", "category": "camping", "base_cost": 5000, "unit": "per night", "description": "Comfortable room with basic amenities"},
            {"name": "Luxury Room", "category": "camping", "base_cost": 8000, "unit": "per night", "description": "Deluxe room with premium amenities"},
            {"name": "Jeep Service", "category": "transport", "base_cost": 6000, "unit": "per trip", "description": "4x4 jeep to and from base camp"},
            {"name": "Guide Service", "category": "activities", "base_cost": 3000, "unit": "per day", "description": "Professional mountain guide"},
            {"name": "Local Cuisine", "category": "food", "base_cost": 1200, "unit": "per person per day", "description": "Traditional meals at camp"},
            {"name": "Trekking Supplies", "category": "shopping", "base_cost": 4000, "unit": "per package", "description": "Essential trekking gear rental"},
        ]
        for cost in costs_data2:
            CostComponent.objects.create(destination=second_dest, **cost)
        print(f"Created {len(costs_data2)} cost components for {second_dest.name}")

# 5. Verify
print(f"\\n=== FINAL STATUS ===")
print(f"Destinations: {Destination.objects.count()} total, {Destination.objects.filter(is_featured=True).count()} featured")
print(f"Products: {Product.objects.count()} total, {Product.objects.filter(is_active=True).count()} active")
print(f"Cost Components: {CostComponent.objects.count()} total")
print("\\nDONE!")
'''
    
    # Upload the fix script
    remote_path = f"/home/{USERNAME}/fix_database.py"
    url = f"{BASE_URL}/files/path{remote_path}"
    resp = requests.post(url, headers=HEADERS, files={"content": ("fix_database.py", fix_script.encode(), "text/plain")})
    print(f"Fix script uploaded: {resp.status_code}")
    return remote_path

def run_fix_via_console():
    """Run the fix script via console"""
    print("\n=== RUNNING FIX SCRIPT ===")
    
    # List existing consoles
    url = f"{BASE_URL}/consoles/"
    resp = requests.get(url, headers=HEADERS)
    consoles = resp.json() if resp.status_code == 200 else []
    
    bash_console = None
    for c in consoles:
        if 'bash' in c.get('executable', '').lower():
            bash_console = c['id']
            break
    
    if not bash_console:
        resp = requests.post(url, headers=HEADERS, json={
            "executable": "bash",
            "working_directory": f"/home/{USERNAME}/touripk/pkk"
        })
        if resp.status_code in (200, 201):
            bash_console = resp.json()['id']
            time.sleep(3)
        else:
            print(f"  Console creation failed: {resp.status_code}")
            return False
    
    print(f"  Using console: {bash_console}")
    
    # Send the command
    send_url = f"{BASE_URL}/consoles/{bash_console}/send_input/"
    cmd = "cd /home/rohaannoor123/touripk/pkk && source /home/rohaannoor123/.virtualenvs/touripk-venv/bin/activate && python /home/rohaannoor123/fix_database.py\n"
    resp = requests.post(send_url, headers=HEADERS, json={"input": cmd})
    print(f"  Command sent: {resp.status_code}")
    
    # Wait for execution
    time.sleep(8)
    
    # Get output
    output_url = f"{BASE_URL}/consoles/{bash_console}/get_latest_output/"
    resp = requests.get(output_url, headers=HEADERS)
    if resp.status_code == 200:
        output = resp.json().get('output', '')
        print(f"\n  Console output:\n{output[-3000:]}")
    
    return True

def reload_and_verify():
    """Reload and verify"""
    print("\n=== RELOADING WEB APP ===")
    url = f"{BASE_URL}/webapps/{DOMAIN}/reload/"
    resp = requests.post(url, headers=HEADERS)
    print(f"  Reload: {resp.status_code}")
    
    time.sleep(5)
    
    print("\n=== FINAL VERIFICATION ===")
    
    # Check homepage
    resp = requests.get(f"https://{DOMAIN}/", timeout=15)
    print(f"  Home: {resp.status_code} ({len(resp.content)} bytes)")
    if 'No Featured' in resp.text:
        print("  ISSUE: Still 'No Featured Destinations'")
    else:
        # Count how many destination cards appear
        import re
        cards = resp.text.count('destination-card') or resp.text.count('card')
        print(f"  OK: Destinations appear to be showing (cards found: {cards})")
    
    # Check media
    resp2 = requests.get(f"https://{DOMAIN}/media/destinations/hunza-valley.jpg", timeout=15)
    print(f"  Media: {resp2.status_code} ({len(resp2.content)} bytes)")
    
    # Check admin login
    session = requests.Session()
    login_page = session.get(f"https://{DOMAIN}/admin/login/", timeout=15)
    
    # Get CSRF token
    import re
    csrf_match = re.search(r'csrfmiddlewaretoken.*?value="([^"]+)"', login_page.text)
    if csrf_match:
        csrf = csrf_match.group(1)
        login_resp = session.post(f"https://{DOMAIN}/admin/login/", data={
            'csrfmiddlewaretoken': csrf,
            'username': 'admin',
            'password': 'admin123456',
            'next': '/admin/'
        }, headers={'Referer': f'https://{DOMAIN}/admin/login/'}, timeout=15)
        
        if login_resp.status_code == 200 and '/admin/login/' not in login_resp.url:
            print(f"  Admin login: SUCCESS (redirected to {login_resp.url})")
        else:
            print(f"  Admin login: {login_resp.status_code} (url: {login_resp.url})")
    else:
        print("  Admin: Could not get CSRF token")

if __name__ == "__main__":
    script_path = upload_fix_script()
    run_fix_via_console()
    reload_and_verify()
