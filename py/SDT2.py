#!/usr/bin/env python3
"""
lm_sdt_automation.py

Puts LogicMonitor Devices and Device Instances into Scheduled Downtime (SDT),
reading the list of targets from a CSV file, and writes a result report to
an Excel (.xlsx) file.

Requirements:
    pip install logicmonitor_sdk openpyxl

LogicMonitor credentials (LMv1 API key):
    Set these as environment variables (recommended), or pass as CLI args:
        LM_COMPANY     - your LogicMonitor portal/company name
        LM_ACCESS_ID   - API access id
        LM_ACCESS_KEY  - API access key

CSV input format (header row required), one row per SDT target:

    type,device_name,datasource_name,instance_name,duration_minutes,start_datetime,end_datetime,comment

    type              : "device" or "instance"
    device_name       : device display name (or IP/hostname) as shown in LM
    datasource_name   : datasource name (only required when type=instance)
    instance_name     : instance name (only required when type=instance)
    duration_minutes  : used when start/end are left blank -> SDT starts "now"
                         and runs for this many minutes
    start_datetime     : optional, format YYYY-MM-DD HH:MM (local time). If
                          provided, overrides "now" as the SDT start.
    end_datetime        : optional, format YYYY-MM-DD HH:MM (local time). If
                          provided with start_datetime, overrides duration_minutes.
    comment           : free text comment stored on the SDT

Example rows:
    device,web-prod-01,,,,60,,,Patch window
    instance,db-prod-02,MySQL_Replication,slave1,,2026-08-25 22:00,2026-08-25 23:00,DB maintenance

Usage:
    python lm_sdt_automation.py --input targets.csv --output sdt_report.xlsx

Notes / assumptions about the SDK (please verify against your installed
version -- LogicMonitor periodically renames filter fields):
  - Device lookup uses api.get_device_list(filter='displayName:"<name>"')
    and falls back to filter='name:"<name>"' (IP/hostname) if nothing found.
  - Datasource-on-device lookup uses api.get_device_data_source_list(device_id,
    filter='dataSourceName:"<name>"') to get the HDS (host datasource) id.
  - Instance lookup uses api.get_device_data_source_instance_list(device_id,
    hds_id, filter='name:"<name>"') to get the instance id.
  - SDT creation uses api.add_sdt(body=...) with logicmonitor_sdk.DeviceSDT
    or logicmonitor_sdk.DeviceDataSourceInstanceSDT model objects, sdt_type=1
    (one-time SDT) with explicit start/end epoch millis.
  If any of these calls/filters don't match your SDK build, run
  `python -c "import logicmonitor_sdk; print(dir(logicmonitor_sdk.LMApi))"`
  to see the exact method names available and adjust the two lookup
  functions below accordingly -- the rest of the script (CSV/Excel handling,
  flow, reporting) does not need to change.
"""

import argparse
import csv
import os
import sys
import time
import logging
from datetime import datetime, timedelta

try:
    import logicmonitor_sdk
    from logicmonitor_sdk.rest import ApiException
except ImportError:
    print("Missing dependency: pip install logicmonitor_sdk", file=sys.stderr)
    sys.exit(1)

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
except ImportError:
    print("Missing dependency: pip install openpyxl", file=sys.stderr)
    sys.exit(1)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("lm_sdt")

DATETIME_FMT = "%Y-%m-%d %H:%M"


# --------------------------------------------------------------------------
# LogicMonitor API helpers
# --------------------------------------------------------------------------

def build_api_client(company, access_id, access_key):
    configuration = logicmonitor_sdk.Configuration()
    configuration.company = company
    configuration.access_id = access_id
    configuration.access_key = access_key
    return logicmonitor_sdk.LMApi(logicmonitor_sdk.ApiClient(configuration))


def find_device(api, device_name):
    """Return the LM device object matching device_name, or None."""
    for field in ("displayName", "name"):
        try:
            resp = api.get_device_list(filter='{}:"{}"'.format(field, device_name))
        except ApiException as e:
            log.debug("Device lookup by %s failed: %s", field, e)
            continue
        items = getattr(resp, "items", None) or []
        if items:
            return items[0]
    return None


def find_instance(api, device_id, datasource_name, instance_name):
    """Return (hds_id, instance_id) for a device/datasource/instance, or (None, None)."""
    try:
        ds_resp = api.get_device_data_source_list(
            device_id, filter='dataSourceName:"{}"'.format(datasource_name)
        )
    except ApiException as e:
        log.debug("Datasource lookup failed: %s", e)
        return None, None

    ds_items = getattr(ds_resp, "items", None) or []
    if not ds_items:
        return None, None
    hds_id = ds_items[0].id

    try:
        inst_resp = api.get_device_data_source_instance_list(
            device_id, hds_id, filter='name:"{}"'.format(instance_name)
        )
    except ApiException as e:
        log.debug("Instance lookup failed: %s", e)
        return hds_id, None

    inst_items = getattr(inst_resp, "items", None) or []
    if not inst_items:
        return hds_id, None
    return hds_id, inst_items[0].id


def to_epoch_millis(dt):
    return int(time.mktime(dt.timetuple()) * 1000)


def resolve_window(row):
    """Return (start_dt, end_dt) as datetime objects based on row values."""
    start_raw = (row.get("start_datetime") or "").strip()
    end_raw = (row.get("end_datetime") or "").strip()
    duration_raw = (row.get("duration_minutes") or "").strip()

    if start_raw and end_raw:
        start_dt = datetime.strptime(start_raw, DATETIME_FMT)
        end_dt = datetime.strptime(end_raw, DATETIME_FMT)
        return start_dt, end_dt

    duration = int(duration_raw) if duration_raw else 60  # default 1 hour
    start_dt = datetime.strptime(start_raw, DATETIME_FMT) if start_raw else datetime.now()
    end_dt = start_dt + timedelta(minutes=duration)
    return start_dt, end_dt


def create_device_sdt(api, device_id, start_dt, end_dt, comment):
    body = logicmonitor_sdk.DeviceSDT(
        type="DeviceSDT",
        sdt_type=1,  # one-time SDT
        device_id=device_id,
        start_date_time=to_epoch_millis(start_dt),
        end_date_time=to_epoch_millis(end_dt),
        comment=comment or "Created by lm_sdt_automation.py",
    )
    return api.add_sdt(body=body)


def create_instance_sdt(api, instance_id, start_dt, end_dt, comment):
    body = logicmonitor_sdk.DeviceDataSourceInstanceSDT(
        type="DeviceDataSourceInstanceSDT",
        sdt_type=1,
        device_data_source_instance_id=instance_id,
        start_date_time=to_epoch_millis(start_dt),
        end_date_time=to_epoch_millis(end_dt),
        comment=comment or "Created by lm_sdt_automation.py",
    )
    return api.add_sdt(body=body)


# --------------------------------------------------------------------------
# Main processing
# --------------------------------------------------------------------------

REQUIRED_COLUMNS = {"type", "device_name"}


def read_targets(csv_path):
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError("CSV is missing required column(s): {}".format(missing))
        return list(reader)


def process_row(api, row):
    """Process a single CSV row. Returns a result dict for the report."""
    result = dict(row)
    result["status"] = "Failed"
    result["sdt_id"] = ""
    result["start_used"] = ""
    result["end_used"] = ""
    result["message"] = ""

    row_type = (row.get("type") or "").strip().lower()
    device_name = (row.get("device_name") or "").strip()

    if row_type not in ("device", "instance"):
        result["message"] = "Invalid type (must be 'device' or 'instance')"
        return result
    if not device_name:
        result["message"] = "device_name is required"
        return result

    try:
        start_dt, end_dt = resolve_window(row)
    except ValueError as e:
        result["message"] = "Bad start/end/duration value: {}".format(e)
        return result

    result["start_used"] = start_dt.strftime(DATETIME_FMT)
    result["end_used"] = end_dt.strftime(DATETIME_FMT)

    device = find_device(api, device_name)
    if device is None:
        result["message"] = "Device not found: {}".format(device_name)
        return result

    comment = (row.get("comment") or "").strip()

    try:
        if row_type == "device":
            sdt = create_device_sdt(api, device.id, start_dt, end_dt, comment)
            result["status"] = "Success"
            result["sdt_id"] = getattr(sdt, "id", "")
            result["message"] = "Device SDT created"
        else:
            ds_name = (row.get("datasource_name") or "").strip()
            inst_name = (row.get("instance_name") or "").strip()
            if not ds_name or not inst_name:
                result["message"] = "datasource_name and instance_name are required for type=instance"
                return result

            hds_id, instance_id = find_instance(api, device.id, ds_name, inst_name)
            if instance_id is None:
                result["message"] = "Instance not found: {} / {} / {}".format(
                    device_name, ds_name, inst_name
                )
                return result

            sdt = create_instance_sdt(api, instance_id, start_dt, end_dt, comment)
            result["status"] = "Success"
            result["sdt_id"] = getattr(sdt, "id", "")
            result["message"] = "Instance SDT created"
    except ApiException as e:
        result["message"] = "API error: {}".format(e.reason or e)
    except Exception as e:  # noqa: BLE001 - report any unexpected failure per-row
        result["message"] = "Unexpected error: {}".format(e)

    return result


# --------------------------------------------------------------------------
# Excel report
# --------------------------------------------------------------------------

REPORT_COLUMNS = [
    ("type", "Type"),
    ("device_name", "Device Name"),
    ("datasource_name", "Datasource"),
    ("instance_name", "Instance"),
    ("start_used", "SDT Start"),
    ("end_used", "SDT End"),
    ("status", "Status"),
    ("sdt_id", "SDT ID"),
    ("message", "Message"),
]


def write_report(results, output_path):
    wb = Workbook()
    ws = wb.active
    ws.title = "SDT Report"

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    success_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    fail_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

    for col_idx, (_, header) in enumerate(REPORT_COLUMNS, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    for row_idx, result in enumerate(results, start=2):
        for col_idx, (key, _) in enumerate(REPORT_COLUMNS, start=1):
            ws.cell(row=row_idx, column=col_idx, value=result.get(key, ""))
        fill = success_fill if result.get("status") == "Success" else fail_fill
        for col_idx in range(1, len(REPORT_COLUMNS) + 1):
            ws.cell(row=row_idx, column=col_idx).fill = fill

    # Reasonable column widths
    widths = [10, 22, 18, 18, 17, 17, 10, 10, 40]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    ws.freeze_panes = "A2"
    wb.save(output_path)


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Bulk-create LogicMonitor SDTs from a CSV file.")
    parser.add_argument("--input", required=True, help="Path to input CSV file")
    parser.add_argument("--output", required=True, help="Path to output Excel report")
    parser.add_argument("--company", default=os.environ.get("LM_COMPANY"), help="LM portal/company name")
    parser.add_argument("--access-id", default=os.environ.get("LM_ACCESS_ID"), help="LM API access id")
    parser.add_argument("--access-key", default=os.environ.get("LM_ACCESS_KEY"), help="LM API access key")
    args = parser.parse_args()

    if not all([args.company, args.access_id, args.access_key]):
        log.error(
            "Missing LM credentials. Set LM_COMPANY/LM_ACCESS_ID/LM_ACCESS_KEY "
            "env vars or pass --company/--access-id/--access-key."
        )
        sys.exit(1)

    try:
        rows = read_targets(args.input)
    except (OSError, ValueError) as e:
        log.error("Failed to read input CSV: %s", e)
        sys.exit(1)

    log.info("Loaded %d target(s) from %s", len(rows), args.input)

    api = build_api_client(args.company, args.access_id, args.access_key)

    results = []
    for i, row in enumerate(rows, start=1):
        log.info(
            "[%d/%d] Processing %s '%s'...",
            i, len(rows), row.get("type"), row.get("device_name"),
        )
        result = process_row(api, row)
        results.append(result)
        log.info("  -> %s: %s", result["status"], result["message"])

    write_report(results, args.output)
    log.info("Report written to %s", args.output)

    success_count = sum(1 for r in results if r["status"] == "Success")
    log.info("Done: %d succeeded, %d failed out of %d", success_count, len(results) - success_count, len(results))


if __name__ == "__main__":
    main()
