#!/usr/bin/env python3

import csv
import os
from datetime import datetime
import logicmonitor_sdk
from logicmonitor_sdk.rest import ApiException


# =========================
# Configuration
# =========================

INPUT_FILE = "sdt_input.csv"
LOG_FILE = "sdt_log.csv"

LM_COMPANY = os.environ["LM_COMPANY"]
LM_ACCESS_ID = os.environ["LM_ACCESS_ID"]
LM_ACCESS_KEY = os.environ["LM_ACCESS_KEY"]

DATE_FORMAT = "%Y-%m-%d %H:%M"


# =========================
# LogicMonitor SDK setup
# =========================

configuration = logicmonitor_sdk.Configuration()

configuration.company = LM_COMPANY
configuration.access_id = LM_ACCESS_ID
configuration.access_key = LM_ACCESS_KEY

api_client = logicmonitor_sdk.ApiClient(configuration)
lm_api = logicmonitor_sdk.LMApi(api_client)


# =========================
# Helpers
# =========================

def date_to_epoch_ms(date_string):
    """
    Convert CSV date/time to epoch milliseconds.
    """

    dt = datetime.strptime(date_string.strip(), DATE_FORMAT)

    return int(dt.timestamp() * 1000)


def find_device(device_name):
    """
    Find a LogicMonitor device by display name.
    """

    filter_value = f'name:"{device_name}"'

    response = lm_api.get_devices(
        filter=filter_value,
        size=100
    )

    devices = response.data.items

    for device in devices:
        if device.name.lower() == device_name.lower():
            return device

    return None


def create_sdt(device, start, end, comment):
    """
    Create a one-time Device SDT.
    """

    body = logicmonitor_sdk.SDT(
        type="DeviceSDT",
        sdt_type="oneTime",
        start_date_time=start,
        end_date_time=end,
        comment=comment
    )

    # Device SDT requires the device ID.
    body.device_id = device.id

    return lm_api.add_sdt(body)


# =========================
# Process CSV
# =========================

log_rows = []

with open(INPUT_FILE, "r", newline="", encoding="utf-8-sig") as csv_file:

    reader = csv.DictReader(csv_file)

    for row_number, row in enumerate(reader, start=2):

        device_name = row["device"].strip()
        start_string = row["start"].strip()
        end_string = row["end"].strip()
        comment = row.get("comment", "").strip()

        try:

            # Validate dates
            start = date_to_epoch_ms(start_string)
            end = date_to_epoch_ms(end_string)

            if end <= start:
                raise ValueError("End time must be after start time")

            # Find device
            device = find_device(device_name)

            if device is None:
                raise ValueError("Device not found")

            # Create SDT
            response = create_sdt(
                device,
                start,
                end,
                comment
            )

            sdt_id = getattr(response.data, "id", "")

            print(
                f"[SUCCESS] {device_name} "
                f"(ID {device.id}) "
                f"SDT {sdt_id}"
            )

            log_rows.append({
                "device": device_name,
                "device_id": device.id,
                "start": start_string,
                "end": end_string,
                "status": "SUCCESS",
                "sdt_id": sdt_id,
                "message": "SDT created",
            })

        except Exception as e:

            print(
                f"[FAILED] {device_name}: {e}"
            )

            log_rows.append({
                "device": device_name,
                "device_id": "",
                "start": start_string,
                "end": end_string,
                "status": "FAILED",
                "sdt_id": "",
                "message": str(e),
            })


# =========================
# Write log
# =========================

with open(LOG_FILE, "w", newline="", encoding="utf-8") as log_file:

    fieldnames = [
        "device",
        "device_id",
        "start",
        "end",
        "status",
        "sdt_id",
        "message"
    ]

    writer = csv.DictWriter(
        log_file,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(log_rows)


print()
print(f"Finished. Log written to: {LOG_FILE}")