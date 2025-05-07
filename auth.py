# ---------------------------------------------
# Module: auth.py
# Author: Your Name
# Version: 1.0
# Date: 2025-05-07
#
# Requirements:
# - Python 3.x
# - requests library (`pip install requests`)
# - A JSON file named `credentials.json` in the same directory
#
# Expected credentials.json format:
# {
#   "accessId": "your_access_id",
#   "accessKey": "your_access_key",
#   "api_url": "https://yourcompany.logicmonitor.com/santagateway/api/v1/auth"
# }
#
# Description:
# This script authenticates with the LogicMonitor API using credentials
# and API URL loaded from a JSON file. On success, it prints an auth token.
# ---------------------------------------------

import requests
import json

# Function to load credentials and API URL from JSON
def get_credentials():
    with open('credentials.json', 'r') as file:
        credentials = json.load(file)
    return credentials

# Load credentials and API URL from file
credentials = get_credentials()
accessId = credentials['accessId']
accessKey = credentials['accessKey']
api_url = credentials['api_url']  # <-- Now loaded from file

# Authentication payload
auth_data = {
    'accessId': accessId,
    'accessKey': accessKey
}

# Send POST request to authenticate
response = requests.post(api_url, json=auth_data)

# Handle response
if response.status_code == 200:
    print("Authentication successful!")
    auth_token = response.json().get("data", {}).get("authToken")
    print(f"Authentication token: {auth_token}")
else:
    print(f"Authentication failed with status code {response.status_code}")
    print(response.text)
