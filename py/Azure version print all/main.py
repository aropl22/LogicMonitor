#!/usr/bin/env python3

import json
import logicmonitor_sdk
from logicmonitor_sdk.rest import ApiException
from auth_sdk_env import api_auth_from_env

def main():

    #Authentication
    api_instance = api_auth_from_env()

    #load config
    with open('config.json') as f:
        config = json.load(f)

    GROUP_NAME = config['group_name']
    print(f"Group Name:{GROUP_NAME}")

    # Get device group Id
    try: 

        api_response = api_instance.get_device_group_list(filter=f'name:"{GROUP_NAME}"')
        data = api_response.to_dict()
        group_id = data['items'][0]['id']
        print(f"Group ID: {group_id}\n")

    except ApiException as e:
        print("Exception when calling AccessGroupApi->getAccessGroupList: %s\n" % e)

    try: 

    # Get devices in the group

        all_devices = []
        offset = 0
        page_size = 50

        print(f"Device list: \n")
        
        # Pagination
        while True:
            page = api_instance.get_immediate_device_list_by_device_group_id(
                group_id,
                size=page_size,
                offset=offset
                )
            all_devices.extend(page.items)
            if offset + page_size >= page.total:
                break
            offset += page_size

        ## Print all values
        #for device in all_devices:
        #    print(f"device ID: {device.id} \n {device} \n")

        ## Print device ID, Name, IP address
        for device in all_devices:
            print(f"{device.id} - {device.display_name} - {device.auto_properties[0].value}")

    except ApiException as e:
        print("Exception when calling AccessGroupApi->getAccessGroupList: %s\n" % e)

if __name__ == "__main__":
    main()
  