
#!/usr/bin/env python3

import json
from pathlib import Path

import logicmonitor_sdk


CREDENTIALS = "credentials.json"
DASHBOARD_DIR = Path("./lm-dashboards")
TARGET_GROUP = "LogicMonitor Dashboards test"


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


def get_target_group(api_instance):

    result = api_instance.get_dashboard_group_list(
        size=1000
    )

    groups = get_value(result, "items", [])

    for group in groups:

        group_name = get_value(
            group,
            "name"
        )

        if group_name == TARGET_GROUP:

            group_id = get_value(
                group,
                "id"
            )

            if group_id is None:
                raise RuntimeError(
                    f"Dashboard group '{TARGET_GROUP}' "
                    "has no ID."
                )

            print(
                f"Target group: {TARGET_GROUP}"
            )

            print(
                f"Target group ID: {group_id}"
            )

            print()

            return group_id, groups

    raise RuntimeError(
        f"Dashboard group '{TARGET_GROUP}' "
        "was not found."
    )


def get_child_group_ids(
    groups,
    parent_id
):

    child_ids = set()

    for group in groups:

        group_parent_id = get_value(
            group,
            "parentId"
        )

        group_id = get_value(
            group,
            "id"
        )

        if (
            str(group_parent_id)
            == str(parent_id)
        ):

            child_ids.add(
                group_id
            )

            # Recursively find subfolders
            child_ids.update(
                get_child_group_ids(
                    groups,
                    group_id
                )
            )

    return child_ids


def get_existing_dashboards(
    api_instance,
    target_group_id,
    groups
):

    # Start with the target group
    valid_group_ids = {
        target_group_id
    }

    # Add all subgroups/subfolders
    valid_group_ids.update(
        get_child_group_ids(
            groups,
            target_group_id
        )
    )

    print(
        f"Dashboard groups included: "
        f"{len(valid_group_ids)}"
    )

    print()

    result = api_instance.get_dashboard_list(
        size=1000
    )

    items = get_value(
        result,
        "items",
        []
    )

    dashboards = {}

    for dashboard in items:

        dashboard_group_id = get_value(
            dashboard,
            "groupId"
        )

        # Only include dashboards that are
        # in target group or its subgroups
        if dashboard_group_id not in valid_group_ids:
            continue

        dashboard_name = get_value(
            dashboard,
            "name"
        )

        if dashboard_name:

            dashboards[dashboard_name] = dashboard

    return dashboards


def create_dashboard(
    api_instance,
    dashboard,
    group_id
):

    body = {
        "name": dashboard["name"],
        "groupId": group_id,
        "template": dashboard
    }

    api_instance.add_dashboard(
        body
    )


def update_dashboard(
    api_instance,
    dashboard_id,
    dashboard
):

    api_instance.update_dashboard_by_id(
        dashboard_id,
        dashboard
    )


def main():

    # ---------------------------------------------------------
    # Connect to LogicMonitor
    # ---------------------------------------------------------

    api_instance = api_auth(
        CREDENTIALS
    )

    # ---------------------------------------------------------
    # Find target group and all dashboard groups
    # ---------------------------------------------------------

    group_id, groups = get_target_group(
        api_instance
    )

    # ---------------------------------------------------------
    # Get dashboards from target group and ALL subfolders
    # ---------------------------------------------------------

    existing_dashboards = get_existing_dashboards(
        api_instance,
        group_id,
        groups
    )

    print(
        f"Existing dashboards under "
        f"'{TARGET_GROUP}': "
        f"{len(existing_dashboards)}"
    )

    print()

    # ---------------------------------------------------------
    # Find all JSON files recursively
    # ---------------------------------------------------------

    json_files = sorted(
        DASHBOARD_DIR.rglob("*.json")
    )

    print(
        f"Found {len(json_files)} dashboard JSON files."
    )

    print()

    # ---------------------------------------------------------
    # Counters
    # ---------------------------------------------------------

    created = 0
    updated = 0
    failed = 0

    # ---------------------------------------------------------
    # Process dashboards
    # ---------------------------------------------------------

    for json_file in json_files:

        try:

            # Read JSON
            with json_file.open(
                "r",
                encoding="utf-8"
            ) as f:

                dashboard = json.load(f)

            # Dashboard name from JSON
            dashboard_name = dashboard.get(
                "name"
            )

            if not dashboard_name:

                print(
                    f"SKIP: {json_file} "
                    "- no dashboard name"
                )

                continue

            print(
                f"Processing: {json_file}"
            )

            print(
                f"Dashboard: {dashboard_name}"
            )

            # -------------------------------------------------
            # Dashboard exists somewhere under target group
            # -------------------------------------------------

            if dashboard_name in existing_dashboards:

                existing = existing_dashboards[
                    dashboard_name
                ]

                dashboard_id = get_value(
                    existing,
                    "id"
                )

                existing_group_id = get_value(
                    existing,
                    "groupId"
                )

                print(
                    f"  EXISTS - updating "
                    f"dashboard ID {dashboard_id}"
                )

                print(
                    f"  Existing group ID: "
                    f"{existing_group_id}"
                )

                update_dashboard(
                    api_instance,
                    dashboard_id,
                    dashboard
                )

                updated += 1

            # -------------------------------------------------
            # Dashboard doesn't exist anywhere under target
            # group
            # -------------------------------------------------

            else:

                print(
                    "  NOT FOUND - creating dashboard "
                    f"in '{TARGET_GROUP}'"
                )

                create_dashboard(
                    api_instance,
                    dashboard,
                    group_id
                )

                created += 1

            print(
                "  OK"
            )

            print()

        except Exception as e:

            failed += 1

            print(
                f"  ERROR: {e}"
            )

            print()

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    print(
        "----------------------------------------"
    )

    print(
        "Dashboard update complete"
    )

    print(
        "----------------------------------------"
    )

    print(
        f"Target group: {TARGET_GROUP}"
    )

    print(
        f"Group ID    : {group_id}"
    )

    print(
        f"JSON files  : {len(json_files)}"
    )

    print(
        f"Created     : {created}"
    )

    print(
        f"Updated     : {updated}"
    )

    print(
        f"Failed      : {failed}"
    )

    print(
        "----------------------------------------"
    )


if __name__ == "__main__":
    main()
