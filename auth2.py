import requests
import json
import time
import hmac
import hashlib
import base64
from datetime import datetime, timedelta

# Load credentials and account info from config file
with open('config.json', 'r') as f:
    config = json.load(f)

ACCESS_ID = config['access_id']
ACCESS_KEY = config['access_key']
ACCOUNT = config['account']  # Your LogicMonitor subdomain

def build_headers(http_verb, resource_path):
    epoch = str(int(time.time() * 1000))
    request_vars = http_verb + epoch + resource_path
    digest = hmac.new(ACCESS_KEY.encode('utf-8'), msg=request_vars.encode('utf-8'), digestmod=hashlib.sha256).digest()
    signature = base64.b64encode(digest).decode()
    return {
        'Authorization': f'LMv1 {ACCESS_ID}:{signature}:{epoch}',
        'Content-Type': 'application/json'
    }

# Example API call to verify authentication
def test_auth():
    resource_path = '/santaba/rest/device/groups'
    http_verb = 'GET'
    url = f'https://{ACCOUNT}.logicmonitor.com{resource_path}'

    headers = build_headers(http_verb, resource_path)
    response = requests.get(url, headers=headers)

    print("Status Code:", response.status_code)
    if response.status_code == 200:
        print("Authentication successful.")
        print("Response preview:", response.json().get('data', {}).get('items', [])[:1])  # Preview one item
    else:
        print("Authentication failed.")
        print("Response:", response.text)

test_auth()