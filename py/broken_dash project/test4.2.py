# ============================
# ⚠️ WORK IN PROGRESS FILE ⚠️
#   Do not use in production
# ============================

# Script: dashboard-backup
# Author: SA
# Version: 1.0
# Date: 2025-05-23

"""
This script backs up all dashboards from a LogicMonitor account by retrieving
dashboard groups and their associated dashboards using the LogicMonitor SDK v3.
Each dashboard's configuration is saved as a JSON file in a timestamped folder
for versioned backups and auditing.

Requirements:
- logicmonitor-sdk v3
- Valid LogicMonitor API credentials

Outputs:
- JSON files for each dashboard, saved in a uniquely named folder with the current date and time.
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

#request_count = 0
#window_start = time.time()

widgets_config = {}
report = {"groups":{}}
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
report_folder = f"report_{timestamp}"

def throttle(headerinfo):
    lm_api_remaining = int(headerinfo.get('x-rate-limit-remaining'))
    lm_api_limit = int(headerinfo.get('x-rate-limit-limit'))
    lm_api_window = int(headerinfo.get('x-rate-limit-window'))
    #print(f"lm_api_limit: {lm_api_limit}")
    print(f"\rAPI Rate limit Remaining: {lm_api_remaining}/500\033[K", end="", flush=True) #\033[K clears the rest of the line
    #print(f"lm_api_window: {lm_api_window}")
    if lm_api_remaining <2:
      print(f"\nRate limit is almost reached, sleeping for {lm_api_window} seconds")
      time.sleep(lm_api_window)
      #time.sleep(5)

def is_widget_broken(api_instance, w_id):
    try:
        widget_data_http = api_instance.get_widget_data_by_id_with_http_info(w_id)
        widget_data = widget_data_http[0]
        headerinfo = widget_data_http[2]

        throttle(headerinfo=headerinfo)

        if w_id == "2716":
            print(f"Widget ID {w_id} full datahttp response:\n {widget_data_http}")

        # Graphs / tables / Pie charts
        if hasattr(widget_data, "items"):
            if not widget_data.items:
                return True, "resource does not exist / empty list"
            return False, "OK"

        # BigNumberWidget
        elif hasattr(widget_data, "value"):
            if widget_data.value is None:
                return True, "resource does not exist / empty list"
            return False, "OK"
        elif hasattr(widget_data, "data") and isinstance(widget_data.data, list):
            for item in widget_data.data:
                if getattr(item, "value", None) is None:
                    return True, "resource does not exist / empty list"
            return False, "OK"

        # HTML Widget
        elif hasattr(widget_data, "html"):
            if not widget_data.html:
                return True, "resource does not exist / empty HTML"
            return False, "OK"
        elif hasattr(widget_data, "content"):
            if not widget_data.content:
                return True, "resource does not exist / empty HTML"
            return False, "OK"

        # DynamicTableWidgetData
        elif hasattr(widget_data, "rows"):
            if not widget_data.rows:
                return True, "resource does not exist / empty table"
            return False, "OK"

        # Unknown type
        else:
            return True, f"unexpected widget type: {type(widget_data)}"

    except ApiException as e:
        if "404" in str(e):
            return True, "resource does not exist / empty list"
        return True, f"API error: {e}"

    except Exception as e:
        return True, f"unexpected error: {e}"


def extract_error_message(error_tuple):
    broken, message = error_tuple
    if message is None:
        return None

    # Try to extract LM JSON error
    match = re.search(r'HTTP response body:\s*(\{.*\})', message, re.DOTALL)
    if match:
        try:
            error_json = json.loads(match.group(1))
            return error_json.get("errorMessage") or message
        except json.JSONDecodeError:
            return message

    return message


def is_widget_broken(api_instance, w_id):
    try:
        # Call LM API
        data_http = api_instance.get_widget_data_by_id_with_http_info(w_id)
        data = data_http[0]
        headerinfo = data_http[2]

        # rate limiting
        throttle(headerinfo=headerinfo)

        # ---- Widget type: Graph/Table-based (contain .items)
        if hasattr(data, "items"):
            if data.items is None:
                return True, "items is None (bad response)"
            if isinstance(data.items, list) and len(data.items) == 0:
                return True, "items[] empty — referenced resource missing"
            return False, "Widget OK"

        # ---- Widget type: BigNumber / Single Value (contain .value)
        elif hasattr(data, "value"):
            if data.value is None:
                return True, "value is None — referenced resource missing"
            return False, "Widget OK"

        # ---- Unexpected LM response
        else:
            return True, f"Unexpected widget type: {type(data)}"

    except ApiException as e:
        # Strong detection of missing underlying LM resource
        if "404" in str(e):
            return True, "404: Referenced resource does not exist"
        return True, f"API error: {e}"

    except Exception as e:
        return True, f"Unhandled error: {e}"


def main():

    # Authentication
    api_instance = api_auth("credentials.json")

    #timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    #report_folder = f"report_{timestamp}"
    os.makedirs(report_folder, exist_ok=True)

    # Get all dashboard groups
    try:

        #dashboard_groups = api_instance.get_dashboard_group_list(size=1000).items
        dashboard_groups_http = api_instance.get_dashboard_group_list_with_http_info(size=1000)
        dashboard_groups = dashboard_groups_http[0].items
        headerinfo1 = dashboard_groups_http[2]
        throttle(headerinfo=headerinfo1)

    except ApiException as e:
        print(f"Error fetching dashboard groups: {e}")
        exit(1)

    #print(f"found {len(dashboard_groups)} dashboard groups\n")

    # Loop through all groups and their dashboards
    for group in dashboard_groups:
        group_id = group.id
        group_name = group.name
        report["groups"].setdefault(group_id, {"group_name":group_name,"dashboards":{}})

        try:

            #dashboards = api_instance.get_dashboard_list(filter=f"groupId:{group_id}", size=1000).items
            dashboards_http = api_instance.get_dashboard_list_with_http_info(filter=f"groupId:{group_id}", size=1000)
            dashboards = dashboards_http[0].items
            headerinfo2 = dashboards_http[2]
            throttle(headerinfo=headerinfo2)

        except ApiException as e:
            print(f"Error fetching dashboards for group '{group_name}': {e}")
            continue

        #print(f"{group.name} - \t\t{len(dashboards)} dashboards")
        
        # Print all dashboards from group wait for ENTER before printing next group
       # for dashboard in dashboards:
          #  print(f"{dashboard.full_name} ID {dashboard.id}")

        for dashboard in dashboards:
            dashboard_id = dashboard.id
            dashboard_name = dashboard.name
            dashboard_full_path = dashboard.full_name
            
            try:
                # Get full dashboard config
                dashboard_detail_http = api_instance.get_dashboard_by_id_with_http_info(dashboard_id)
                dashboard_detail = dashboard_detail_http[0]
                headerinfo3 = dashboard_detail_http[2]
                throttle(headerinfo=headerinfo3)
                widgets_config = dashboard_detail.to_dict().get("widgets_config",{})
                #print(f"widget config:\n{widgets_config}")
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

                for w_id in widgets_ids:
                    #widget_detail = api_instance.get_widget_by_id(w_id)
                    widget_detail_http = api_instance.get_widget_by_id_with_http_info(w_id)
                    widget_detail = widget_detail_http[0]
                    headerinfo4 = widget_detail_http[2]
                    widget_name = widget_detail.name
                    widget_type_field = type(widget_detail).__name__
                    throttle(headerinfo=headerinfo4)
                    #report["groups"][group_id]["dashboards"][dashboard_id]["widgets"][w_id] = widget_detail.to_dict()

                    #DEBUG code
                    '''
                    if w_id == "1857":
                        print(f"Widget ID {w_id} full http response:\n {widget_detail_http}")
                    if w_id == "19":
                        print(f"Widget ID {w_id} full http response:\n {widget_detail_http}")
                    '''
                    if w_id == "2716":
                        print(f"Widget ID {w_id} full http response:\n {widget_detail_http}")
                    #END DEBUG code

                    #check if widget is HTML type
                    if "HtmlWidget" in widget_type_field or hasattr(widget_detail, "html") or hasattr(widget_detail, "content"):
                        widget_status = (False, "HTML widget SKIPPED")
                    else:
                        #print(f"Status: {is_widget_broken(api_instance=api_instance,w_id=w_id)}")
                        widget_status = is_widget_broken(api_instance=api_instance, w_id=w_id)

                    #manual pause
                    #input(f"Checking widget: {widget_detail.name} from {dashboard_name}")
                    
#                   

                    
                    #message = extract_error_message(widget_status)
                    message = widget_status[1] # second element is the error string
                    report["groups"][group_id]["dashboards"][dashboard_id]["widgets"][w_id] = {
                        "widget_name": widget_detail.name,
                        "broken_status": widget_status[0],
                        "widget_type": widget_type_field,
                        "widget_error": message,
                    }
                    #print(f" Testing {group_name}/{dashboard_name}/{widget_name} : type {widget_type_field}")
                    #                   
                    # manual pause
                    #input("Widget details above ^^^ press enter to continue")

                #TESTING - only first dashboard from each group
                #print(" Testing group:", group_name)
                break
                #END TESTING

            except ApiException as e:
                print(f"❌ Failed to fetch or save dashboard {dashboard_name}: {e}")
            
        
    # =============================
    # CSV 1: dashboards.csv
    # =============================
    csv_path = f"{report_folder}/dashboards.csv"
    
    #write header only once
    write_header = not os.path.exists(csv_path) or os.stat(csv_path).st_size == 0

    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["full_path","group_name", "group_id", "dashboard_name", "dashboard_id", "dashboard_tokens", "tokens_strings", "widget_name", "widget_id", "widget_type", "widget_status", "widget_error"])

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
                    #print(f"cvs export: {group_name} - {widget_name} status: {widget_error}")
                    
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
  