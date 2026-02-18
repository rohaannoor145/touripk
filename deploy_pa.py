import requests
import time

token = 'a0a783bc25a51c6cb5c0e9dc42298c6b18165495'
username = 'rohaannoor123'
api_headers = {'Authorization': f'Token {token}'}
base = f'https://www.pythonanywhere.com/api/v0/user/{username}'
webapp = f'{base}/webapps/{username}.pythonanywhere.com'

print("=" * 50)
print("PYTHONANYWHERE DEPLOYMENT")
print("=" * 50)

# Step 1: Upload deploy script via Files API
print("\n[1/5] Uploading deployment script...")
deploy_script = """#!/bin/bash
set -e
echo "=== STARTING DEPLOYMENT ==="

# Clone repository
cd /home/rohaannoor123
rm -rf touripk
git clone https://github.com/rohaannoor145/touripk.git
echo "=== REPO CLONED ==="

# Create virtualenv
python3.10 -m venv /home/rohaannoor123/.virtualenvs/touripk-venv
echo "=== VENV CREATED ==="

# Install dependencies
source /home/rohaannoor123/.virtualenvs/touripk-venv/bin/activate
pip install --upgrade pip
pip install django python-decouple django-ratelimit argon2-cffi djangorestframework djangorestframework-simplejwt django-cors-headers django-taggit channels django-filter stripe google-generativeai requests
echo "=== DEPENDENCIES INSTALLED ==="

# Create .env file
cat > /home/rohaannoor123/touripk/pkk/.env << 'ENVEOF'
SECRET_KEY=django-insecure-k)6^82w2l%f9(pj1g%nak4niqu=w4(a!+4zp$v@k2fblfy777h
DEBUG=False
ENVEOF
echo "=== ENV FILE CREATED ==="

# Run migrations
cd /home/rohaannoor123/touripk/pkk
python manage.py migrate --noinput
echo "=== MIGRATIONS DONE ==="

# Collect static files
mkdir -p /home/rohaannoor123/touripk/pkk/staticfiles
python manage.py collectstatic --noinput
echo "=== STATIC FILES COLLECTED ==="

echo "=== DEPLOYMENT COMPLETE ==="
"""

r = requests.post(
    f'{base}/files/path/home/{username}/deploy.sh',
    headers=api_headers,
    files={'content': ('deploy.sh', deploy_script.encode())}
)
print(f"  Deploy script uploaded: {r.status_code}")

# Step 2: Upload WSGI configuration
print("\n[2/5] Configuring WSGI...")
wsgi_content = """
import os
import sys

# Add project directory to sys.path
project_home = '/home/rohaannoor123/touripk/pkk'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'touripk.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
"""

# Write WSGI file
wsgi_path = f'/var/www/{username}_pythonanywhere_com_wsgi.py'
r = requests.post(
    f'{base}/files/path{wsgi_path}',
    headers=api_headers,
    files={'content': ('wsgi.py', wsgi_content.encode())}
)
print(f"  WSGI file written: {r.status_code}")

# Step 3: Configure webapp settings
print("\n[3/5] Configuring web app...")
config_updates = {
    'source_directory': '/home/rohaannoor123/touripk/pkk',
    'working_directory': '/home/rohaannoor123/touripk/pkk',
    'virtualenv_path': f'/home/{username}/.virtualenvs/touripk-venv',
    'force_https': True,
}
r = requests.patch(webapp + '/', headers=api_headers, data=config_updates)
print(f"  Web app configured: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"  Source dir: {data.get('source_directory')}")
    print(f"  Virtualenv: {data.get('virtualenv_path')}")

# Step 4: Configure static files mapping
print("\n[4/5] Setting up static files...")
# Get current static mappings
r = requests.get(f'{webapp}/static_files/', headers=api_headers)
existing = r.json()
print(f"  Existing mappings: {len(existing)}")

# Delete existing
for sf in existing:
    sf_id = sf.get('id')
    if sf_id:
        requests.delete(f'{webapp}/static_files/{sf_id}/', headers=api_headers)

# Add static files mapping
r = requests.post(f'{webapp}/static_files/', headers=api_headers, data={
    'url': '/static/',
    'path': '/home/rohaannoor123/touripk/pkk/staticfiles'
})
print(f"  Static mapping: {r.status_code}")

# Add media files mapping
r = requests.post(f'{webapp}/static_files/', headers=api_headers, data={
    'url': '/media/',
    'path': '/home/rohaannoor123/touripk/pkk/media'
})
print(f"  Media mapping: {r.status_code}")

# Step 5: Create console for user to click
print("\n[5/5] Creating deployment console...")
r = requests.post(f'{base}/consoles/', headers=api_headers, data={
    'executable': 'bash',
    'working_directory': '/home/rohaannoor123',
    'arguments': ''
})
console = r.json()
cid = console['id']
print(f"  Console ID: {cid}")

print("\n" + "=" * 50)
print("CONFIGURATION COMPLETE!")
print("=" * 50)
print(f"\nWeb app: https://{username}.pythonanywhere.com")
print(f"\n>>> TO COMPLETE DEPLOYMENT <<<")
print(f"Open this URL in your browser:")
print(f"  https://www.pythonanywhere.com/user/{username}/consoles/{cid}/")
print(f"\nThen run this command in the console:")
print(f"  bash /home/{username}/deploy.sh")
print(f"\nAfter deployment finishes, reload the web app:")
print(f"  Or run: curl -X POST '{webapp}/reload/' -H 'Authorization: Token {token}'")
