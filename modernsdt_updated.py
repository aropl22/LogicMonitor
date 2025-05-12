from __future__ import print_function
import getpass
from datetime import datetime
import pytz
import logicmonitor_sdk
from logicmonitor_sdk.rest import ApiException
from csv_loader import load_csv_columns  # 👈 import your module

# --- Authentication ---
configuration = logicmonitor_sdk.Configuration()
configuration.company = input("Enter your company name (subdomain only): ")
configuration.access_id = getpass.getpass("Enter your AccessId: ")
configuration.access_key = getpass.getpass("Enter your AccessKey: ")

api_client = logicmonitor_sdk.ApiClient(configuration)
device_api = logicmonitor_sdk.DeviceApi(api_client)
sdt_api = logicmonitor_sdk.SDTApi(api_client)

# --- Time conversion helper ---
def to_epoch_millis(dt_str):
    eastern = pytz.timezone("America/New_York")
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    dt = eastern.localize(dt)
    dt_utc = dt.astimezone(pytz.utc)
    return int(dt_utc.timestamp() * 1000)

# --- Load CSV ---
csv_file = "devices.csv"
columns_needed = ['Name', 'Start', 'End']

try:
    rows = load_csv_columns(csv_file, columns_needed)
except ValueError as e:
    print(f"Error loading CSV: {e}")
    exit(1)

# --- Schedule SDT ---
for row in rows:
    device_name = row['Name']
    start_time = to_epoch_millis(row['Start'])
    end_time = to_epoch_millis(row['End'])

    try:
        # Search device
        filter_str = f"displayName:\"{device_name}\""
        result = device_api.get_devices(filter=filter_str)

        if not result.items:
            print(f"[NOT FOUND] Device: {device_name}")
            continue

        device_id = result.items[0].id

        # Create and send SDT
        sdt = logicmonitor_sdk.SDT(
            type="DeviceSDT",
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
            comment="Scheduled via script"
        )
        sdt_api.add_sdt(sdt)

        print(f"[OK] SDT scheduled for '{device_name}' ({row['Start']} to {row['End']})")

    except ApiException as e:
        print(f"[ERROR] {device_name}: {e}")
