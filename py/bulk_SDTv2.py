#!/usr/bin/env python3

import csv
import os
import json
from datetime import datetime
import logicmonitor_sdk
from logicmonitor_sdk.rest import ApiException
from auth_sdk import api_auth


# =========================
# Configuration
# =========================

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
INPUT_FILE = "sdt_input.csv"
LOG_FILE = f"sdt_log_{timestamp}.csv"
DATE_FORMAT = "%Y-%m-%d %H:%M"
CREDENTIALS = "credentials sandbox.json"

#REPORT_FOLDER = f"report_{timestamp}"


# =========================
# LogicMonitor SDK setup / Authentication
# =========================

api_instance = api_auth(CREDENTIALS)
#api_instance = api_auth("credentials-sandbox-write.json")
#api_instance = api_auth("credentials-prod-read.json")
#os.makedirs(REPORT_FOLDER, exist_ok=True)

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

    #filter_value = f'displayName:"{device_name}"'
    #filter_value = f'displayName:"{device_name}"'
    filter_value = f'name:"{device_name}"' #FQDN

    response = api_instance.get_device_list(
        filter=filter_value,
        size=10
    )

    devices = response.items

    for device in devices:
        #if device.display_name.lower() == device_name.lower():
        if device.name.lower() == device_name.lower():
            #print (f"found device: {device}")
            #print(dir(device))
            return device

    return None


def create_sdt(device, start, end, comment):
    """
    Create a one-time Device SDT.
    """
    body = {
            #"type":"DeviceSDT",
            "type":"ResourceSDT",
            "sdtType":"oneTime",
            "startDateTime":start,
            "endDateTime":end,
            "comment":comment,
            "deviceId":device.id
    }

    result = api_instance.add_sdt(body)
    

    #print(f"add_sdt response: {result}")
    return result



def main():

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

                #sdt_id = getattr(response, "id", "")
                sdt_id = response.id if response else ""

                print(
                    f"[SUCCESS] {device_name} "
                    f"(ID {device.id}) "
                    f"SDT ID {sdt_id}"
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
                    "device_id": getattr(device, "id", ""),
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

if __name__ == "__main__":
    main()
