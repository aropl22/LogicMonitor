import csv

from logicmonitor_sdk import Configuration, ApiClient
from logicmonitor_sdk.api.alert_api import AlertApi
from logicmonitor_sdk.models.add_alert_note_request import AddAlertNoteRequest
from logicmonitor_sdk.rest import ApiException


# -------------------------
# LogicMonitor Configuration
# -------------------------
config = Configuration(
    company="your_company",
    access_id="your_access_id",
    access_key="your_access_key"
)

client = ApiClient(config)
alert_api = AlertApi(client)


# -------------------------
# CSV File
# -------------------------
CSV_FILE = "AlertNotes.csv"


with open(CSV_FILE, mode="r", newline="", encoding="utf-8") as file:

    reader = csv.DictReader(file)

    for row in reader:

        alert_id = row["AlertID"]
        note = row["Note"]

        if not alert_id or not note:
            continue

        try:
            body = AddAlertNoteRequest(
                note=note
            )

            alert_api.add_alert_note(
                id=int(alert_id),
                add_alert_note_request=body
            )

            print(f"✓ Added note to alert {alert_id}")

        except ApiException as e:
            print(f"✗ Failed alert {alert_id}: {e}")