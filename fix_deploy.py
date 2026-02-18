import requests

token = 'a0a783bc25a51c6cb5c0e9dc42298c6b18165495'
headers = {'Authorization': f'Token {token}'}
base = 'https://www.pythonanywhere.com/api/v0/user/rohaannoor123'

deploy_script = """#!/bin/bash
set -e
echo "=== STARTING DEPLOYMENT ==="

cd /home/rohaannoor123
rm -rf touripk
git clone https://github.com/rohaannoor145/touripk.git
echo "=== REPO CLONED ==="

python3.10 -m venv /home/rohaannoor123/.virtualenvs/touripk-venv
echo "=== VENV CREATED ==="

source /home/rohaannoor123/.virtualenvs/touripk-venv/bin/activate
pip install --upgrade pip
pip install django python-decouple django-ratelimit argon2-cffi djangorestframework djangorestframework-simplejwt django-cors-headers django-taggit channels django-filter stripe google-generativeai requests Pillow
echo "=== DEPENDENCIES INSTALLED ==="

cat > /home/rohaannoor123/touripk/pkk/.env << 'ENVEOF'
SECRET_KEY=django-insecure-k)6^82w2l%f9(pj1g%nak4niqu=w4(a!+4zp$v@k2fblfy777h
DEBUG=False
ENVEOF
echo "=== ENV FILE CREATED ==="

cd /home/rohaannoor123/touripk/pkk
python manage.py migrate --noinput
echo "=== MIGRATIONS DONE ==="

mkdir -p /home/rohaannoor123/touripk/pkk/staticfiles
python manage.py collectstatic --noinput
echo "=== STATIC FILES COLLECTED ==="

echo "=== DEPLOYMENT COMPLETE ==="
"""

r = requests.post(
    f'{base}/files/path/home/rohaannoor123/deploy.sh',
    headers=headers,
    files={'content': ('deploy.sh', deploy_script.encode())}
)
print(f'Deploy script updated: {r.status_code}')
