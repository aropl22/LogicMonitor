#!/usr/bin/env python3

"""
Script Name: get_group_inventory_by_name.py
Description:
    Loads LogicMonitor API credentials and a group name from JSON,
    then prints all devices in that group.
"""

import json
import logicmonitor_sdk
from logicmonitor_sdk.rest import ApiException

# --- Load config ---
with open('config.json') as f:
    config = json.load(f)

ACCESS_ID = config['access_id']
ACCESS_KEY = config['access_key']
COMPANY = config['company']
TARGET_GROUP_NAME = config['group_name']

# --- Configure API client ---
configuration = logicmonitor_sdk.Configuration()
configuration.access_id = ACCESS_ID
configuration.access_key = ACCESS_KEY
configuration.company = COMPANY

api_client = logicmonitor_sdk.ApiClient(configuration)
device_api = logicmonitor_sdk.DeviceApi(api_client)
device_group_api = logicmonitor_sdk.DeviceGroupApi(api_client)

try:
    # Step 1: Get all device groups and match by name
    groups_response = device_group_api.get_device_groups()
    matching_groups = [g for g in groups_response.data.items if g.name == TARGET_GROUP_NAME]

    if not matching_groups:
        print(f"No group found with name: {TARGET_GROUP_NAME}")
        exit(1)

    group = matching_groups[0]
    group_id = group.id
    print(f"\nFound group '{group.name}' (ID: {group_id})\n")

    # Step 2: Get devices in the group
    device_response = device_api.get_devices(filter=f"groupId:{group_id}")
    devices = device_response.data.items

    print(f"Devices in group '{TARGET_GROUP_NAME}':")
    if devices:
        for device in devices:
            print(f"  - {device.display_name} (hostname: {device.name})")
    else:
        print("  [No devices found]")

except ApiException as e:
    print("API Exception:", e)
