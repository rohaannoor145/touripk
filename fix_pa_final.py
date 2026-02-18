"""Check and fix PythonAnywhere static/media mappings, and load fixture data"""
import requests
import time

API_TOKEN = "a0a783bc25a51c6cb5c0e9dc42298c6b18165495"
USERNAME = "rohaannoor123"
BASE_URL = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}
DOMAIN = f"{USERNAME}.pythonanywhere.com"

def check_static_mappings():
    """Check current static file mappings"""
    print("=== CHECKING STATIC FILE MAPPINGS ===")
    url = f"{BASE_URL}/webapps/{DOMAIN}/static_files/"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        mappings = resp.json()
        for m in mappings:
            print(f"  {m['url']} -> {m['path']} (id: {m['id']})")
        return mappings
    else:
        print(f"  Error: {resp.status_code}")
        return []

def ensure_media_mapping():
    """Ensure /media/ mapping exists"""
    print("\n=== ENSURING MEDIA MAPPING ===")
    url = f"{BASE_URL}/webapps/{DOMAIN}/static_files/"
    resp = requests.get(url, headers=HEADERS)
    mappings = resp.json() if resp.status_code == 200 else []
    
    has_media = any(m['url'] == '/media/' for m in mappings)
    if has_media:
        print("  /media/ mapping already exists")
    else:
        print("  Adding /media/ mapping...")
        resp = requests.post(url, headers=HEADERS, json={
            "url": "/media/",
            "path": "/home/rohaannoor123/touripk/pkk/media"
        })
        print(f"  Result: {resp.status_code} {resp.text[:200]}")

def load_fixtures_via_console():
    """Try to load fixtures by creating a console and running commands"""
    print("\n=== LOADING FIXTURE DATA VIA CONSOLE ===")
    
    # First, list existing consoles
    url = f"{BASE_URL}/consoles/"
    resp = requests.get(url, headers=HEADERS)
    consoles = resp.json() if resp.status_code == 200 else []
    print(f"  Existing consoles: {len(consoles)}")
    
    # Check if there's already a bash console to reuse
    bash_console = None
    for c in consoles:
        if 'bash' in c.get('executable', '').lower():
            bash_console = c['id']
            print(f"  Reusing console {bash_console}")
            break
    
    if not bash_console:
        # Create a new console
        resp = requests.post(url, headers=HEADERS, json={
            "executable": "bash",
            "arguments": "",
            "working_directory": f"/home/{USERNAME}/touripk/pkk"
        })
        if resp.status_code in (200, 201):
            bash_console = resp.json()['id']
            print(f"  Created console {bash_console}")
            time.sleep(3)  # Wait for console to initialize
        else:
            print(f"  Console creation failed: {resp.status_code} {resp.text[:200]}")
            return False
    
    # Send commands to load data
    send_url = f"{BASE_URL}/consoles/{bash_console}/send_input/"
    
    commands = [
        "cd /home/rohaannoor123/touripk/pkk",
        "source /home/rohaannoor123/.virtualenvs/touripk-venv/bin/activate",
        "python manage.py loaddata content/fixtures/initial_data.json",
        "python manage.py loaddata content/fixtures/destination_costs.json",
        # Create superuser
        'echo "from users.models import CustomUser; CustomUser.objects.filter(username=\'admin\').delete(); u = CustomUser.objects.create_superuser(\'admin\', \'admin@touripk.com\', \'admin123456\'); print(f\'Created: {u.username}\')" | python manage.py shell',
    ]
    
    for cmd in commands:
        print(f"  Sending: {cmd[:80]}...")
        resp = requests.post(send_url, headers=HEADERS, json={"input": cmd + "\n"})
        if resp.status_code != 200:
            print(f"    Failed: {resp.status_code} {resp.text[:100]}")
        time.sleep(2)
    
    # Wait and get output
    time.sleep(5)
    output_url = f"{BASE_URL}/consoles/{bash_console}/get_latest_output/"
    resp = requests.get(output_url, headers=HEADERS)
    if resp.status_code == 200:
        output = resp.json().get('output', '')
        print(f"\n  Console output:\n{output[-2000:]}")
    
    return True

def reload_and_verify():
    """Reload webapp and verify"""
    print("\n=== RELOADING WEB APP ===")
    url = f"{BASE_URL}/webapps/{DOMAIN}/reload/"
    resp = requests.post(url, headers=HEADERS)
    print(f"  Reload: {resp.status_code}")
    
    time.sleep(5)
    
    print("\n=== VERIFYING SITE ===")
    site_url = f"https://{DOMAIN}/"
    resp = requests.get(site_url, timeout=15)
    print(f"  Home: {resp.status_code} ({len(resp.content)} bytes)")
    
    if 'No Featured' in resp.text:
        print("  WARNING: Still 'No Featured Destinations' - fixtures may not be loaded yet")
    elif 'destination' in resp.text.lower() or 'hunza' in resp.text.lower() or 'featured' in resp.text.lower():
        print("  SUCCESS: Destinations content found!")
    
    # Check a media file
    media_url = f"https://{DOMAIN}/media/destinations/hunza-valley.jpg"
    resp2 = requests.get(media_url, timeout=15)
    print(f"  Media test (hunza-valley.jpg): {resp2.status_code} ({len(resp2.content)} bytes)")
    
    # Check admin
    admin_url = f"https://{DOMAIN}/admin/"
    resp3 = requests.get(admin_url, timeout=15)
    print(f"  Admin: {resp3.status_code}")

if __name__ == "__main__":
    check_static_mappings()
    ensure_media_mapping()
    load_fixtures_via_console()
    reload_and_verify()
