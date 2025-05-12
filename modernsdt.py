from __future__ import print_function
import csv
import time
import getpass
from datetime import datetime
import pytz
import logicmonitor_sdk
from logicmonitor_sdk.rest import ApiException

# --- Authentication ---
configuration = logicmonitor_sdk.Configuration()
configuration.company = input("Enter your company name (subdomain only): ")
configuration.access_id = getpass.getpass("Enter your AccessId: ")
configuration.access_key = getpass.getpass("Enter your AccessKey: ")

api_client = logicmonitor_sdk.ApiClient(configuration)
device_api = logicmonitor_sdk.DeviceApi(api_client)
sdt_api = logicmonitor_sdk.SDTApi(api_client)

# --- Helper: convert to epoch millis ---
def to_epoch_millis(dt_str):
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    dt = pytz.utc.localize(dt)  # assumes times are UTC
    return int(dt.timestamp() * 1000)

# --- Read CSV and schedule SDT ---
csv_file = "devices.csv"  # Replace with your file path

with open(csv_file, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        device_name = row['Name']
        start_time = to_epoch_millis(row['Start'])
        end_time = to_epoch_millis(row['End'])

        try:
            # Find device by name
            filter_str = f"displayName:\"{device_name}\""
            result = device_api.get_devices(filter=filter_str)

            if not result.items:
                print(f"Device not found: {device_name}")
                continue

            device_id = result.items[0].id

            # Create SDT object
            sdt = logicmonitor_sdk.SDT(
                type="DeviceSDT",
                device_id=device_id,
                start_time=start_time,
                end_time=end_time,
                comment="Scheduled from CSV script"
            )

            # Submit SDT
            response = sdt_api.add_sdt(sdt)
            print(f"SDT scheduled for '{device_name}' from {row['Start']} to {row['End']}")

        except ApiException as e:
            print(f"API Exception for '{device_name}': {e}")
