import requests

token = 'a0a783bc25a51c6cb5c0e9dc42298c6b18165495'
headers = {'Authorization': f'Token {token}'}
base = 'https://www.pythonanywhere.com/api/v0/user/rohaannoor123'

# Upload script to load fixture data
load_data_script = """#!/bin/bash
source /home/rohaannoor123/.virtualenvs/touripk-venv/bin/activate
cd /home/rohaannoor123/touripk/pkk

echo "=== Loading initial data ==="
python manage.py loaddata content/fixtures/initial_data.json
echo "=== Loading destination costs ==="
python manage.py loaddata content/fixtures/destination_costs.json

echo "=== Creating superuser ==="
echo "from users.models import CustomUser; CustomUser.objects.filter(username='admin').exists() or CustomUser.objects.create_superuser('admin', 'admin@touripk.com', 'Admin@12345', full_name='Admin User')" | python manage.py shell

echo "=== DATA LOADED ==="
"""

r = requests.post(
    f'{base}/files/path/home/rohaannoor123/load_data.sh',
    headers=headers,
    files={'content': ('load_data.sh', load_data_script.encode())}
)
print(f'Load data script uploaded: {r.status_code}')
