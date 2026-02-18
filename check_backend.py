import requests

token = 'a0a783bc25a51c6cb5c0e9dc42298c6b18165495'
headers = {'Authorization': f'Token {token}'}
base = 'https://www.pythonanywhere.com/api/v0/user/rohaannoor123'

# Upload a script to create superuser
create_admin_script = """#!/bin/bash
source /home/rohaannoor123/.virtualenvs/touripk-venv/bin/activate
cd /home/rohaannoor123/touripk/pkk

# Create superuser non-interactively
echo "from users.models import CustomUser; CustomUser.objects.filter(username='admin').exists() or CustomUser.objects.create_superuser('admin', 'admin@touripk.com', 'Admin@12345', full_name='Admin User')" | python manage.py shell

echo "=== SUPERUSER CREATED ==="
echo "Username: admin"
echo "Password: Admin@12345"
"""

r = requests.post(
    f'{base}/files/path/home/rohaannoor123/create_admin.sh',
    headers=headers,
    files={'content': ('create_admin.sh', create_admin_script.encode())}
)
print(f'Admin script uploaded: {r.status_code}')

# Check backend endpoints
print("\nChecking backend endpoints...")
endpoints = [
    '/',
    '/admin/',
    '/api/',
]
for ep in endpoints:
    try:
        r = requests.get(f'https://rohaannoor123.pythonanywhere.com{ep}', timeout=10, allow_redirects=True)
        print(f'  {ep} -> {r.status_code}')
    except Exception as e:
        print(f'  {ep} -> Error: {e}')
