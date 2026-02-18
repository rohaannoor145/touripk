import requests

token = 'a0a783bc25a51c6cb5c0e9dc42298c6b18165495'
headers = {'Authorization': f'Token {token}'}
base = 'https://www.pythonanywhere.com/api/v0/user/rohaannoor123'

# Check error log
r = requests.get(f'{base}/files/path/var/log/rohaannoor123.pythonanywhere.com.error.log', headers=headers)
if r.status_code == 200:
    lines = r.text.strip().split('\n')
    # Show last 50 lines
    print("=== ERROR LOG (last 50 lines) ===")
    for line in lines[-50:]:
        print(line)
else:
    print(f'Error log status: {r.status_code}')
    print(r.text[:500])

# Check server log
print("\n=== SERVER LOG ===")
r2 = requests.get(f'{base}/files/path/var/log/rohaannoor123.pythonanywhere.com.server.log', headers=headers)
if r2.status_code == 200:
    lines2 = r2.text.strip().split('\n')
    for line in lines2[-20:]:
        print(line)
else:
    print(f'Server log status: {r2.status_code}')

# Check access log
print("\n=== ACCESS LOG (last 10) ===")
r3 = requests.get(f'{base}/files/path/var/log/rohaannoor123.pythonanywhere.com.access.log', headers=headers)
if r3.status_code == 200:
    lines3 = r3.text.strip().split('\n')
    for line in lines3[-10:]:
        print(line)
else:
    print(f'Access log status: {r3.status_code}')
