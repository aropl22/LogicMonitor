
#!/usr/bin/env python3

import json
import os
import sys

import logicmonitor_sdk
from logicmonitor_sdk.rest import ApiException
from auth_sdk import api_auth_from_env


def main():
    # Authentication using Azure Pipeline environment variables
    try:
        api_instance = api_auth_from_env()
    except (ValueError, RuntimeError) as e:
        print(f"Authentication configuration error: {e}")
        sys.exit(1)

    # Load configuration
    with open("config.json", encoding="utf-8") as f:
        config = json.load(f)

    group_name = config["group_name"]
    print(f"Group Name: {group_name}")

    # Get device group ID
    try:
        response = api_instance.get_device_group_list(
            filter=f'name:"{group_name}"'
        )

        groups = response.items or []

        if not groups:
            print(f"Device group not found: {group_name}")
            sys.exit(1)

        group_id = groups[0].id
        print(f"Group ID: {group_id}\n")

    except ApiException as e:
        print(f"Error retrieving device group: {e}")
        sys.exit(1)

    # Get devices in the group
    try:
        all_devices = []
        offset = 0
        page_size = 50

        print("Device list:\n")

        # Pagination
        while True:
            page = api_instance.get_immediate_device_list_by_device_group_id(
                group_id,
                size=page_size,
                offset=offset,
            )

            all_devices.extend(page.items or [])

            if offset + page_size >= page.total:
                break

            offset += page_size

        # Print device ID, display name, and IP address
        for device in all_devices:
            ip_address = next(
                (
                    prop.value
                    for prop in (device.auto_properties or [])
                    if prop.name.lower() in ("system.ips", "system.ip")
                ),
                "N/A",
            )

            print(
                f"{device.id} - "
                f"{device.display_name} - "
                f"{ip_address}"
            )

        print(f"\nTotal devices: {len(all_devices)}")

    except ApiException as e:
        print(f"Error retrieving devices: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
