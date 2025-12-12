# Script: dashboard-scanner
# Author: SA
# Version: 1.0
# Date: 2025-12-12

"""
Dashboard-Scanner Script
------------------------

The dashboard-scanner is a Python utility that audits dashboards in a 
LogicMonitor account. It iterates through all dashboard groups, dashboards, 
and widgets, detecting broken or missing widget data, such as empty tables, 
missing graph data, or missing values. The script handles API rate limits by 
tracking the remaining quota and throttling requests when necessary.

Key Features:
-------------
- Enumerates all dashboard groups, dashboards, and widgets.
- Detects broken or incomplete widgets based on type-specific checks.
- Identifies dashboards without widget tokens.
- Skips widgets like HTML or Alert widgets from broken-status checks.
- Tracks API rate limits and throttles requests to avoid exceeding quotas.
- Outputs a CSV report summarizing dashboards, widgets, and their statuses.

Use Cases:
----------
- Identify dashboards with missing or misconfigured widgets.
- Audit widget health across an entire LogicMonitor account.
- Monitor dashboards for potential resource issues without modifying them.

Requirements:
-------------
- Python 3.x
- logicmonitor-sdk v3
- Valid LogicMonitor API credentials (credentials.json)
"""

import json
import re
import os
import csv
import logicmonitor_sdk
import time
from logicmonitor_sdk.rest import ApiException
from auth_sdk import api_auth
from datetime import datetime

REQUEST_LIMIT = 500
WINDOW_SECONDS = 60

widgets_config = {}
report = {"groups":{}}
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
report_folder = f"report_{timestamp}"

def throttle(headerinfo):
    lm_api_remaining = int(headerinfo.get('x-rate-limit-remaining'))
    lm_api_limit = int(headerinfo.get('x-rate-limit-limit'))
    lm_api_window = int(headerinfo.get('x-rate-limit-window'))
    print(f"\rAPI Rate limit Remaining: {lm_api_remaining}/500\033[K", end="", flush=True) #\033[K clears the rest of the line
    if lm_api_remaining <3:
      print(f"\nRate limit is almost reached, sleeping for {lm_api_window/2} seconds")
      time.sleep(lm_api_window/2)

def throttle_tail(headerinfo, obj):
    lm_api_remaining = int(headerinfo.get('x-rate-limit-remaining'))
    lm_api_limit = int(headerinfo.get('x-rate-limit-limit'))
    lm_api_window = int(headerinfo.get('x-rate-limit-window'))
    print(f"\rAPI Rate limit Remaining: {lm_api_remaining}/500\033[K", end="", flush=True) #\033[K clears the rest of the line
    if lm_api_remaining <20:
      print(f"\nRate limit is below 20, sleeping for {lm_api_window/4} seconds before proceed with the next {obj}")
      time.sleep(lm_api_window/4)

def extract_error_message(error_tuple):
    broken, message = error_tuple
    if message is None:
        return None
    #try to extract LM JSON error
    match = re.search(r'HTTP response body:\s*(\{.*\})', message, re.DOTALL)
    if match:
        try:
            error_json = json.loads(match.group(1))
            return error_json.get("errorMessage") or message
        except json.JSONDecodeError:
            return message

    return message

def check_graphplot_widget(widget):
    """
    Handles GraphPlot widgets returned by logicmonitor_sdk.
    The input is usually a GraphPlot object, not a dict.
    """

    # If it's an SDK model with to_dict(), convert it
    if hasattr(widget, "to_dict"):
        widget = widget.to_dict()

    # Now ensure it's a dict
    if not isinstance(widget, dict):
        return True, f"Invalid structure: expected dict after to_dict(), got {type(widget)}"

    # GraphPlot stores data inside 'lines' → each line contains 'data'
    lines = widget.get("lines")
    if not lines or not isinstance(lines, list):
        return True, "Graph widget has no 'lines' or list is empty"

    # Check if any line has meaningful data points
    for line in lines:
        data_points = line.get("data")
        if isinstance(data_points, list) and len(data_points) > 0:
            return False, "OK"

    return True, "Graph has no datapoints in any line"

def extract_numeric_from_big_number(raw_data):
    """
    Recursively extract numeric values from LM BigNumber widget raw data.
    Returns a list of numeric values (can be empty).
    """
    numeric_values = []

    if raw_data is None:
        return numeric_values

    if isinstance(raw_data, (int, float)):
        numeric_values.append(raw_data)
    elif isinstance(raw_data, str):
        try:
            numeric_values.append(float(raw_data))
        except ValueError:
            pass
    elif isinstance(raw_data, list):
        for item in raw_data:
            numeric_values.extend(extract_numeric_from_big_number(item))
    elif isinstance(raw_data, dict):
        for k, v in raw_data.items():
            numeric_values.extend(extract_numeric_from_big_number(v))

    return numeric_values

def check_bignumber_widget(data):
    """
    Handles BigNumber widgets returned by logicmonitor_sdk.
    The input is usually a BigNumber object, not a dict.
    """
    d = data.to_dict()

    # First check top-level 'value'
    if "value" in d and d["value"] is not None:
        try:
            float(d["value"])
            return False, "OK"
        except (ValueError, TypeError):
            pass

    raw_data = d.get("data")

    numeric_values = extract_numeric_from_big_number(raw_data)

    if numeric_values:
        return False, "OK"
    else:
        return True, "No numeric values found (may contain 'No Data')"

def check_piechart_widget(widget):
    """
    Handles PieChart widgets returned by logicmonitor_sdk.
    The input is usually a PieChart object, not a dict.
    """
    # If SDK model → convert
    if hasattr(widget, "to_dict"):
        widget = widget.to_dict()

    # If tuple → extract dict part
    if isinstance(widget, tuple) and len(widget) >= 1:
        widget = widget[0]

    # Must now be a dict
    if not isinstance(widget, dict):
        return True, f"Invalid widget structure: {type(widget)}"

    data_list = widget.get("data")

    # No data[] list at all
    if not isinstance(data_list, list) or len(data_list) == 0:
        return True, "PieChart has no data[] values"

    values = []

    for item in data_list:
        if not isinstance(item, dict):
            continue
        val = item.get("value")
        if isinstance(val, (int, float)):
            values.append(val)

    # No numeric values in the widget
    if not values:
        return True, "PieChart has no numeric values"

    # All values are 0 → error
    if all(v == 0 for v in values):
        return True, "PieChart values are all zero"

    # Otherwise OK
    return False, "OK"

def check_gauge_widget(widget):
    """
    Validates a Gauge widget:
      - current_value must be non-zero and not None
      - history_values must contain at least one numeric non-zero value
    """

    # Convert SDK object
    if hasattr(widget, "to_dict"):
        widget = widget.to_dict()

    # Extract from tuple response
    if isinstance(widget, tuple) and len(widget) >= 1:
        widget = widget[0]

    if not isinstance(widget, dict):
        return True, f"Invalid widget structure: {type(widget)}"

    # --- CURRENT VALUE CHECK ---
    current = widget.get("current_value")

    if current is None:
        return True, "Gauge current_value is None"

    if isinstance(current, (int, float)):
        if current == 0:
            return True, "Gauge current_value is 0"
    else:
        return True, f"Gauge current_value is not numeric: {current}"

    # --- HISTORY VALUES CHECK ---
    history = widget.get("history_values")

    if not isinstance(history, list):
        return True, "Gauge history_values missing or not a list"

    numeric_history = [
        v for v in history if isinstance(v, (int, float))
    ]

    if not numeric_history:
        return True, "Gauge history_values has no numeric entries"

    if all(v == 0 for v in numeric_history):
        return True, "Gauge history_values are all 0"

    # If both checks passed → OK
    return False, "OK"

def check_sla_widget(widget: dict) -> tuple[bool, str]:
    """
    Validate SLA widget structures for DeviceSLA and WebsiteSLA widgets.
    Returns:
        (True, "OK") if valid
        (False, "<reason>") if invalid
    """

    # -------------------------
    # WEBSITE SLA (websiteSLA)
    # -------------------------
    # Convert SDK object → dict
    if hasattr(widget, "to_dict"):
        widget = widget.to_dict()

    # Tuple response: (dict, status, headers)
    if isinstance(widget, tuple) and len(widget) > 0:
        widget = widget[0]

    if not isinstance(widget, dict):
        return False, f"Invalid website SLA widget type: {type(widget)}"

    # Ensure this really is websiteSLA
    if widget.get("type") == "websiteSLA":

        availability = widget.get("availability")

        # Missing field → error
        if availability is None:
            return False, "availability missing"

        # Not numeric → error
        if not isinstance(availability, (int, float)):
            try:
                availability = float(availability)
            except Exception:
                return False, f"availability not numeric: {availability}"

        # Passed all checks → OK
        return True, "OK"

    # -------------------------
    # DEVICE SLA (deviceSLA)
    # -------------------------
    if widget.get("type") == "deviceSLA":
        results = widget.get("result_list", [])
        if not results:
            return False, "result_list missing or empty"

        value = results[0].get("value")

        # Return error for LM errors
        if value == "Group not found":
            return False, "Group not found"

        # None value
        if value is None:
            return False, "value is None"

        # Not numeric
        try:
            value = float(value)
        except Exception:
            return False, f"value not numeric: {value}"

        return True, "OK"

    # -------------------------
    # Unsupported widget type
    # -------------------------
    return False, f"Unsupported widget type: {widget.get('type')}"

def is_widget_broken(api_instance, w_id, widget_type_field):
    """
    Returns (broken_status: bool, message: str)
    Robust detection of broken widgets by type.
    """
    
    # Get widget data with HTTP info
    # Handle "Unhandled error: could not convert string to float: 'No Data'"
    try:
        data_http = api_instance.get_widget_data_by_id_with_http_info(w_id)
        widget_obj = data_http[0]  # actual widget object
        headers = data_http[2]

    except ValueError as e:
            # The SDK is trying to convert "No Data" into float
        if "No Data" in str(e):
            return "Skipped", "No Data"
        return True, f"Widget detail error: {e}"

    except Exception as e:
        return True, f"Widget detail unhandled: {e}"

    # Rate limiting
    #throttle(headers)

    # ------------------------------
    # HTML / Alert widgets → skip
    # ------------------------------
    if "HtmlWidget" in widget_type_field or "AlertWidget" in widget_type_field:
        return False, "SKIPPED"

    # ------------------------------
    # BigNumber / SingleValue → numeric check only
    # ------------------------------
    if widget_type_field in ["BigNumberWidget", "SingleValueWidget"]:
        return check_bignumber_widget(widget_obj)

    # ------------------------------
    # PieChartWidget → list check
    # ------------------------------
    if widget_type_field in ["PieChartWidget"]:
        return check_piechart_widget(widget_obj)
    
    # ------------------------------
    # GaugeWidget → values and historic values check
    # ------------------------------
    if widget_type_field in ["GaugeWidget"]:
        return check_gauge_widget(widget_obj)
    
    # ------------------------------
    # SLAWidget → check value
    # ------------------------------
    if "SLAWidget" in widget_type_field:
        return check_sla_widget(widget_obj)

    # ------------------------------
    # Graph widgets
    # ------------------------------
    if widget_type_field in ["CustomGraphWidget", "GraphPlotWidget"]:
        return check_graphplot_widget(widget_obj)
    # ------------------------------
    # Dynamic Table Widget (rows)
    # ------------------------------
    if hasattr(widget_obj, "rows"):
        if not widget_obj.rows:
            return True, "rows[] empty — referenced resource missing"
        return False, "OK"

    # ------------------------------
    # Generic table (items)
    # ------------------------------
    if hasattr(widget_obj, "items"):
        if not widget_obj.items:
            return True, "items[] empty — referenced resource missing"
        return False, "OK"

    # ------------------------------
    # Catch-all for unknown / unsupported
    # ------------------------------
    return True, f"Unexpected widget type: {type(widget_obj)}"
    '''
    except ApiException as e:
        if "404" in str(e):
            return True, "404: Referenced resource does not exist"
        return True, f"API error: {e}"

    except Exception as e:
        return True, f"Unhandled error: {e}"
    '''

def main():

    # Authentication
    api_instance = api_auth("credentials.json")
    os.makedirs(report_folder, exist_ok=True)

    # Get all dashboard groups
    try:
        dashboard_groups_http = api_instance.get_dashboard_group_list_with_http_info(size=1000)
        dashboard_groups = dashboard_groups_http[0].items
        headerinfo1 = dashboard_groups_http[2]
        throttle(headerinfo=headerinfo1)
    except ApiException as e:
        print(f"Error fetching dashboard groups: {e}")
        exit(1)

    # Loop through all groups and their dashboards
    for group in dashboard_groups:
        group_id = group.id
        group_name = group.name
        report["groups"].setdefault(group_id, {"group_name":group_name,"dashboards":{}})

        try:
            dashboards_http = api_instance.get_dashboard_list_with_http_info(filter=f"groupId:{group_id}", size=1000)
            dashboards = dashboards_http[0].items
            headerinfo2 = dashboards_http[2]
            throttle(headerinfo=headerinfo2)
        except ApiException as e:
            print(f"Error fetching dashboards for group '{group_name}': {e}")
            continue
        
        # Loop through all dashboards in the group
        for dashboard in dashboards:
            dashboard_id = dashboard.id
            dashboard_name = dashboard.name
            dashboard_full_path = dashboard.full_name
            
            # Get full dashboard config
            try:
                dashboard_detail_http = api_instance.get_dashboard_by_id_with_http_info(dashboard_id)
                dashboard_detail = dashboard_detail_http[0]
                headerinfo3 = dashboard_detail_http[2]
                throttle(headerinfo=headerinfo3)
                widgets_config = dashboard_detail.to_dict().get("widgets_config",{})
                widgets_ids = list(widgets_config.keys())
                report["groups"][group_id]["dashboards"].setdefault(
                    dashboard_id,
                    {
                        "dashboard_name": dashboard_name,
                        "dashboard_full_path": dashboard_full_path,
                        "widget_tokens": [dashboard.widget_tokens],
                        "widgets": {}
                    }
                )

                # Loop through all widgets in the dashboard
                for w_id in widgets_ids:
                    
                    # Handle "Unhandled error: could not convert string to float: 'No Data'"
                    try:
                        widget_detail_http = api_instance.get_widget_by_id_with_http_info(w_id)
                        widget_detail = widget_detail_http[0]
                    
                    except ValueError as e:
                         # The SDK is trying to convert "No Data" into float
                        if "No Data" in str(e):
                            return "Skipped", "No Data"
                        return True, f"Widget detail error: {e}"

                    except Exception as e:
                        return True, f"Widget detail unhandled: {e}"
                
                    headerinfo4 = widget_detail_http[2]
                    widget_name = widget_detail.name
                    widget_type_field = type(widget_detail).__name__
                    throttle(headerinfo=headerinfo4)
                    print(f" | Proceed: {dashboard_name} / {widget_name}")

                    #DEBUG code
                    '''
                    if w_id == "1857":
                        print(f"Widget ID {w_id} full http response:\n {widget_detail_http}")
                    if w_id == "19":
                        print(f"Widget ID {w_id} full http response:\n {widget_detail_http}")
                    '''
                    #END DEBUG code

                    #Check if widget is HTML/Alrt type
                    if "HtmlWidget" in widget_type_field or "AlertWidget" in widget_type_field or hasattr(widget_detail, "content"):
                        widget_status = (False, "SKIPPED")
                    else:
                        widget_status = is_widget_broken(api_instance=api_instance, w_id=w_id, widget_type_field=widget_type_field)

                    #DEBUG code manual pause
                    #input(f"Checking widget: {widget_detail.name} from {dashboard_name}")         

                    message = widget_status[1] # second element is the error string
                    report["groups"][group_id]["dashboards"][dashboard_id]["widgets"][w_id] = {
                        "widget_name": widget_detail.name,
                        "broken_status": widget_status[0],
                        "widget_type": widget_type_field,
                        "widget_error": message,
                    }
                
                    # DEBUG code manual pause
                    #input("Widget details above ^^^ press enter to continue")

                #DEBUG TESTING - only first dashboard from each group
                
                #break
                
                #END TESTING

            except ApiException as e:
                print(f"❌ Failed to fetch or save dashboard {dashboard_name}: {e}")
            headerinfo2 = headerinfo4
            headerinfo3 = headerinfo4
        throttle_tail(headerinfo=headerinfo3, obj="dashboard")
    throttle_tail(headerinfo=headerinfo2, obj="group")
            
        
    # =============================
    # CSV 1: dashboards.csv
    # =============================
    csv_path = f"{report_folder}/dashboards.csv"
    
    #Write header only once
    write_header = not os.path.exists(csv_path) or os.stat(csv_path).st_size == 0

    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["full_path","group_name", "group_id", "dashboard_name", "dashboard_id", "dashboard_tokens", "tokens_strings", "widget_name", "widget_id", "widget_type", "broken_widget", "widget_error"])

        for group_id, group_data in report.get("groups", {}).items():
            group_name = group_data.get("group_name", "UNKNOWN")
            
            for dash_id, dash_info in group_data.get("dashboards", {}).items():
                tokens = dash_info.get("widget_tokens") or []
    
                # Flatten list in case it containes inner lists
                
                flat_tokens = []
                for t in tokens:
                    if isinstance(t, list):
                            flat_tokens.extend(t)
                    else:
                            flat_tokens.append(t)

                # Join flatted list to a string
                token_str = ", ".join(str(x) for x in flat_tokens) if flat_tokens else "NONE"
                token_status = "YES" if flat_tokens else "NO"
                
                for widget_id, widget_data in dash_info.get("widgets", {}).items():
                    widget_name = widget_data.get("widget_name", "UNKNOWN")
                    widget_status = widget_data.get("broken_status", "UNKNOWN")
                    widget_error = widget_data.get("widget_error", 'UNKNOWN')
                    
                    writer.writerow([
                        dash_info.get("dashboard_full_path", "UNKNOWN"),
                        group_name,
                        group_id,
                        dash_info.get("dashboard_name", "UNKNOWN"),
                        dash_id,
                        token_status,
                        token_str,
                        widget_name,
                        widget_id,
                        widget_data.get("widget_type", "UNKNOWN"),
                        widget_status,
                        widget_error
                    ])

if __name__ == "__main__":
    main()
