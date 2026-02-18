import requests

token = 'a0a783bc25a51c6cb5c0e9dc42298c6b18165495'
headers = {'Authorization': f'Token {token}'}
base = 'https://www.pythonanywhere.com/api/v0/user/rohaannoor123'
webapp = f'{base}/webapps/rohaannoor123.pythonanywhere.com'

# Set virtualenv path
r = requests.patch(f'{webapp}/', headers=headers, data={
    'virtualenv_path': '/home/rohaannoor123/.virtualenvs/touripk-venv'
})
print(f'Virtualenv set: {r.status_code}')

# Reload the web app
r = requests.post(f'{webapp}/reload/', headers=headers)
print(f'Reload: {r.status_code}')

# Check final config
r = requests.get(f'{webapp}/', headers=headers)
d = r.json()
print(f"Domain: {d.get('domain_name')}")
print(f"Source: {d.get('source_directory')}")
print(f"Virtualenv: {d.get('virtualenv_path')}")
print(f"HTTPS: {d.get('force_https')}")
print(f"Enabled: {d.get('enabled')}")

# Test if site is responding
try:
    r = requests.get('https://rohaannoor123.pythonanywhere.com/', timeout=15)
    print(f"\nSite status: {r.status_code}")
except Exception as e:
    print(f"\nSite check: {e}")
