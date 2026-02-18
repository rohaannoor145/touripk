"""Fix PythonAnywhere deployment errors: upload media files, create superuser, load fixtures"""
import requests
import os
import time

API_TOKEN = "a0a783bc25a51c6cb5c0e9dc42298c6b18165495"
USERNAME = "rohaannoor123"
BASE_URL = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}

PA_PROJECT = f"/home/{USERNAME}/touripk/pkk"
LOCAL_MEDIA = r"c:\Users\s\Desktop\pkk 3.0\pkk\media"

def upload_file(local_path, remote_path):
    """Upload a file to PythonAnywhere"""
    url = f"{BASE_URL}/files/path{remote_path}"
    with open(local_path, 'rb') as f:
        resp = requests.post(url, headers=HEADERS, files={"content": f})
    if resp.status_code in (200, 201):
        print(f"  OK: {remote_path}")
    else:
        print(f"  FAIL ({resp.status_code}): {remote_path} - {resp.text[:100]}")
    return resp.status_code in (200, 201)

def upload_media():
    """Upload all media files"""
    print("=== UPLOADING MEDIA FILES ===")
    
    media_dirs = ['destinations', 'Logos', 'companies', 'packages', 'products']
    
    for dirname in media_dirs:
        local_dir = os.path.join(LOCAL_MEDIA, dirname)
        if not os.path.exists(local_dir):
            continue
            
        files = [f for f in os.listdir(local_dir) if os.path.isfile(os.path.join(local_dir, f))]
        if not files:
            continue
            
        print(f"\n  Uploading {dirname}/ ({len(files)} files)...")
        
        for filename in files:
            local_path = os.path.join(local_dir, filename)
            remote_path = f"{PA_PROJECT}/media/{dirname}/{filename}"
            upload_file(local_path, remote_path)

def run_console_command(command):
    """Run a command in PythonAnywhere console"""
    # Create a new console
    url = f"{BASE_URL}/consoles/"
    resp = requests.post(url, headers=HEADERS, json={
        "executable": "bash",
        "arguments": "",
        "working_directory": PA_PROJECT
    })
    
    if resp.status_code == 201:
        console_id = resp.json()['id']
        print(f"  Console created: {console_id}")
        
        # Send command
        send_url = f"{BASE_URL}/consoles/{console_id}/send_input/"
        resp2 = requests.post(send_url, headers=HEADERS, json={"input": command + "\n"})
        print(f"  Command sent: {resp2.status_code}")
        
        time.sleep(5)
        
        # Get output
        output_url = f"{BASE_URL}/consoles/{console_id}/get_latest_output/"
        resp3 = requests.get(output_url, headers=HEADERS)
        if resp3.status_code == 200:
            print(f"  Output: {resp3.json().get('output', 'No output')[:500]}")
        
        return console_id
    else:
        print(f"  Console creation failed: {resp.status_code} {resp.text[:200]}")
        return None

def create_superuser_script():
    """Upload and run a script to create superuser and load data"""
    print("\n=== CREATING SUPERUSER & LOADING DATA ===")
    
    script = """#!/bin/bash
cd /home/rohaannoor123/touripk/pkk
source /home/rohaannoor123/.virtualenvs/touripk-venv/bin/activate

# Load fixture data
echo "Loading fixtures..."
python manage.py loaddata content/fixtures/initial_data.json 2>&1 || echo "initial_data failed"
python manage.py loaddata content/fixtures/destination_costs.json 2>&1 || echo "destination_costs failed"

# Create superuser
echo "Creating superuser..."
echo "from users.models import CustomUser; u = CustomUser.objects.filter(username='admin').first(); \\
u.delete() if u else None; \\
u = CustomUser.objects.create_superuser(username='admin', email='admin@touripk.com', password='admin123456'); \\
print(f'Superuser created: {u.username}')" | python manage.py shell

echo "Done!"
"""
    
    # Upload the script
    remote_path = f"/home/{USERNAME}/fix_and_load.sh"
    url = f"{BASE_URL}/files/path{remote_path}"
    resp = requests.post(url, headers=HEADERS, files={"content": ("fix_and_load.sh", script.encode(), "text/plain")})
    print(f"  Script uploaded: {resp.status_code}")
    
    return remote_path

def reload_webapp():
    """Reload the web app"""
    print("\n=== RELOADING WEB APP ===")
    domain = f"{USERNAME}.pythonanywhere.com"
    url = f"{BASE_URL}/webapps/{domain}/reload/"
    resp = requests.post(url, headers=HEADERS)
    print(f"  Reload: {resp.status_code}")
    return resp.status_code == 200

def verify_site():
    """Check if the site is working"""
    print("\n=== VERIFYING SITE ===")
    domain = f"{USERNAME}.pythonanywhere.com"
    
    urls_to_check = [
        f"https://{domain}/",
        f"https://{domain}/admin/",
    ]
    
    for url in urls_to_check:
        try:
            resp = requests.get(url, timeout=15)
            print(f"  {url} -> {resp.status_code} ({len(resp.content)} bytes)")
            if url.endswith('/') and url.count('/') == 3:  # Home page
                if 'No Featured' in resp.text:
                    print("    WARNING: Still showing 'No Featured Destinations'")
                elif 'destination' in resp.text.lower() or 'hunza' in resp.text.lower():
                    print("    OK: Destinations are showing!")
        except Exception as e:
            print(f"  {url} -> ERROR: {e}")

if __name__ == "__main__":
    # Step 1: Upload media files
    upload_media()
    
    # Step 2: Upload fix script (user needs to run it in PA console)
    script_path = create_superuser_script()
    
    # Step 3: Reload web app
    reload_webapp()
    
    # Step 4: Verify
    time.sleep(3)
    verify_site()
    
    print(f"\n=== IMPORTANT ===")
    print(f"Media files uploaded. Web app reloaded.")
    print(f"To create superuser & load data, run in PythonAnywhere Bash console:")
    print(f"  bash {script_path}")
    print(f"\nAdmin login: username=admin, password=admin123456")
