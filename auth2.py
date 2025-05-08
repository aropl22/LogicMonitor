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
