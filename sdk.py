from lm import LM

# Initialize LM client with your credentials
lm = LM(access_id='your-access-id',
        access_key='your-access-key',
        account='your-account')  # just the subdomain, e.g., "acme" for acme.logicmonitor.com

# Example: Get all devices
response = lm.get('device/devices')
if response.status == 200:
    devices = response.data.get('items', [])
    print("Devices:", devices)
else:
    print("Error:", response.errmsg)
