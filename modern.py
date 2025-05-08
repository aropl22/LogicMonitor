import logicmonitor_sdk
from logicmonitor_sdk.rest import ApiException
from pprint import pprint

# Configure API credentials
configuration = logicmonitor_sdk.Configuration()
configuration.access_id = 'your-access-id'
configuration.access_key = 'your-access-key'
configuration.company = 'your-account'  # Subdomain only

# Create API client
api_client = logicmonitor_sdk.ApiClient(configuration)

# Instantiate a specific API
device_api = logicmonitor_sdk.DeviceApi(api_client)

# Example: Get devices
try:
    api_response = device_api.get_devices()
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DeviceApi->get_devices: %s\n" % e)
