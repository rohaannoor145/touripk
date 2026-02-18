import requests
import time

token = 'a0a783bc25a51c6cb5c0e9dc42298c6b18165495'
username = 'rohaannoor123'
headers = {'Authorization': f'Token {token}'}
base = f'https://www.pythonanywhere.com/api/v0/user/{username}'
webapp = f'{base}/webapps/{username}.pythonanywhere.com'
console_id = 45201435

print("=" * 50)
print("PYTHONANYWHERE UPDATE (git pull + reload)")
print("=" * 50)

# Step 1: Send the update command to existing console
print(f"\n[1/2] Sending update command to console {console_id}...")
cmd = (
    "cd /home/rohaannoor123/touripk && git pull origin main && "
    "source /home/rohaannoor123/.virtualenvs/touripk-venv/bin/activate && "
    "cd pkk && python manage.py migrate --noinput && "
    "python manage.py collectstatic --noinput && echo ALLDONE\n"
)
r = requests.post(
    f'{base}/consoles/{console_id}/send_input/',
    headers=headers,
    data={'input': cmd}
)
print(f'  Input sent: {r.status_code}')

# Poll for output up to 80 seconds
for i in range(16):
    time.sleep(5)
    out = requests.get(
        f'{base}/consoles/{console_id}/get_latest_output/',
        headers=headers
    )
    if out.status_code == 200:
        output = out.json().get('output', '')
        tail = output[-400:].strip()
        if tail:
            print(f'  [{(i+1)*5}s] ...{tail[-250:]}')
        if 'ALLDONE' in output or 'fatal' in output.lower():
            break

# Step 2: Reload the web app
print("\n[2/2] Reloading web app...")
r = requests.post(f'{webapp}/reload/', headers=headers)
print(f'  Reload: {r.status_code}')

time.sleep(3)
try:
    r = requests.get(f'https://{username}.pythonanywhere.com/', timeout=15)
    print(f'\n  Site status: {r.status_code}')
except Exception as e:
    print(f'\n  Site check error: {e}')

print("\nDone.")

