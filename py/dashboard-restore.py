#!/usr/bin/env python3

import json
from pathlib import Path

import logicmonitor_sdk


CREDENTIALS = "credentials.json"
DASHBOARD_DIR = Path("./lm-dashboards")


def api_auth(credentials):

    with open(credentials, "r", encoding="utf-8") as f:
        config = json.load(f)

    configuration = logicmonitor_sdk.Configuration()
    configuration.access_id = config["accessId"]
    configuration.access_key = config["accessKey"]
    configuration.company = config["account"]

    api_client = logicmonitor_sdk.LMApi(
        logicmonitor_sdk.ApiClient(configuration)
    )

    return api_client


def get_value(obj, key, default=None):

    if isinstance(obj, dict):
        return obj.get(key, default)

    return getattr(obj, key, default)


def get_existing_dashboards(api_instance):

    result = api_instance.get_dashboard_list()

    items = get_value(result, "items", [])

    return {
        get_value(dashboard, "name"): dashboard
        for dashboard in items
        if get_value(dashboard, "name")
    }


def create_dashboard(api_instance, dashboard):

    body = {
        "name": dashboard["name"],
        "template": dashboard
    }

    api_instance.add_dashboard(body)


def update_dashboard(api_instance, dashboard_id, dashboard):

    api_instance.update_dashboard_by_id(
        dashboard_id,
        dashboard
    )


def main():

    # Connect to LogicMonitor
    api_instance = api_auth(CREDENTIALS)

    # Get existing dashboards
    existing_dashboards = get_existing_dashboards(api_instance)

    # Find all JSON files recursively
    json_files = sorted(DASHBOARD_DIR.rglob("*.json"))

    print(f"Found {len(json_files)} dashboard JSON files.")
    print()

    created = 0
    updated = 0
    failed = 0

    for json_file in json_files:

        try:

            # Read JSON
            with json_file.open("r", encoding="utf-8") as f:
                dashboard = json.load(f)

            # Dashboard name from JSON
            dashboard_name = dashboard.get("name")

            if not dashboard_name:
                print(f"SKIP: {json_file} - no dashboard name")
                continue

            print(f"Processing: {json_file}")
            print(f"Dashboard: {dashboard_name}")

            # -------------------------------------------------
            # Dashboard already exists
            # -------------------------------------------------

            if dashboard_name in existing_dashboards:

                existing = existing_dashboards[dashboard_name]
                dashboard_id = get_value(existing, "id")

                print(
                    f"  EXISTS - updating dashboard ID {dashboard_id}"
                )

                update_dashboard(
                    api_instance,
                    dashboard_id,
                    dashboard
                )

                updated += 1

            # -------------------------------------------------
            # Dashboard doesn't exist
            # -------------------------------------------------

            else:

                print("  NOT FOUND - creating dashboard")

                create_dashboard(
                    api_instance,
                    dashboard
                )

                created += 1

            print("  OK")
            print()

        except Exception as e:

            failed += 1

            print(f"  ERROR: {e}")
            print()

    print("----------------------------------------")
    print("Dashboard update complete")
    print("----------------------------------------")
    print(f"JSON files : {len(json_files)}")
    print(f"Created    : {created}")
    print(f"Updated    : {updated}")
    print(f"Failed     : {failed}")
    print("----------------------------------------")


if __name__ == "__main__":
    main()