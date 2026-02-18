"""Deploy fixed views to PythonAnywhere"""
import requests
import time
import os

API_TOKEN = "a0a783bc25a51c6cb5c0e9dc42298c6b18165495"
USERNAME = "rohaannoor123"
BASE_URL = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}
DOMAIN = f"{USERNAME}.pythonanywhere.com"
LOCAL_BASE = r"c:\Users\s\Desktop\pkk 3.0\pkk"

# Files to upload
files_to_upload = {
    "packages/views.py": "packages/views.py",
    "packages/company_views.py": "packages/company_views.py",
    "content/views.py": "content/views.py",
}

for local_rel, remote_rel in files_to_upload.items():
    local_path = os.path.join(LOCAL_BASE, local_rel)
    remote_path = f"/home/{USERNAME}/touripk/pkk/{remote_rel}"
    url = f"{BASE_URL}/files/path{remote_path}"
    with open(local_path, "rb") as f:
        resp = requests.post(url, headers=HEADERS, files={"content": (os.path.basename(local_rel), f)})
    print(f"Uploaded {local_rel}: {resp.status_code}")

# Reload webapp
requests.post(f"{BASE_URL}/webapps/{DOMAIN}/reload/", headers=HEADERS)
print("\nAll files deployed and reloaded.")
