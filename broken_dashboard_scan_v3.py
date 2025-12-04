#!/usr/bin/env python3

from logicmonitor_sdk import configuration, ApiClient
from logicmonitor_sdk.api import lm_api
import json

# -------------------------------
# CONFIGURE YOUR LM CREDENTIALS
# -------------------------------
LM_COMPANY = "your_company"       # e.g., "acme"
LM_ACCESS_ID = "your_access_id"
LM_ACCESS_KEY = "your_access_key"

# -----------------------------------------
# Helper: Detect widget-level error signals
# -----------------------------------------
def is_widget_broken(widget):
    """
    Returns True if the widget is broken (missing resource, instance, or API error).
    """
    error_keys = ["errorMessage", "errorMsg", "error", "validationError"]

    for key in error_keys:
        if key in widget and widget[key]:
            return True

    # Missing resource or instance references
    if widget.get("resourceId") is None and widget.get("type") != "text":
        return True

    if widget.get("instanceId") is None and widget.get("type") not in ("text", "website"):
        return True

    return False

def main():
    # --------------------------
    # API CONFIG
    # --------------------------
    lm_config = configuration.Configuration()
    lm_config.company = LM_COMPANY
    lm_config.access_id = LM_ACCESS_ID
    lm_config.access_key = LM_ACCESS_KEY

    with ApiClient(lm_config) as api_client:
        api = lm_api.LMApi(api_client)

        print("Scanning dashboards for broken widgets...")

        offset = 0
        limit = 100
        broken = []

        while True:
            # GET dashboards list
            dashboards_resp = api.call_api(
                resource_path='/dashboard/dashboards',
                method='GET',
                query_params={'offset': offset, 'size': limit},
                response_type='object'
            )
            dashboards = dashboards_resp.get('items', [])

            if not dashboards:
                break

            for dash in dashboards:
                dash_id = dash.get("id")
                dash_name = dash.get("name", "Unnamed Dashboard")

                # GET dashboard details
                dash_detail = api.call_api(
                    resource_path=f'/dashboard/dashboards/{dash_id}',
                    method='GET',
                    response_type='object'
                )
                widgets = dash_detail.get("widgets", [])

                for w in widgets:
                    if is_widget_broken(w):
                        broken.append({
                            "dashboard_name": dash_name,
                            "dashboard_id": dash_id,
                            "widget_name": w.get("name", "Unnamed Widget"),
                            "widget_id": w.get("id"),
                            "widget_type": w.get("type"),
                            "raw_widget": w,
                        })

            offset += limit

        # --------------------------
        # Output results
        # --------------------------
        if not broken:
            print("\nAll dashboards look good. No broken widgets found.")
        else:
            print("\n=== BROKEN DASHBOARDS FOUND ===\n")
            for item in broken:
                print(f"Dashboard: {item['dashboard_name']} (ID {item['dashboard_id']})")
                print(f"  Widget: {item['widget_name']} (ID {item['widget_id']})")
                print(f"  Type:   {item['widget_type']}\n")

            # Optional: save full details to JSON
            with open("broken_dashboards.json", "w") as f:
                json.dump(broken, f, indent=2)

            print('Saved full details to "broken_dashboards.json".')

if __name__ == "__main__":
    main()
