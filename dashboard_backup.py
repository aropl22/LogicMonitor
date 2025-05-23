# ==========================
# ⚠️ WORK IN PROGRESS FILE ⚠️
# Do not use in production
# ==========================

import os
import json
from logicmonitor_sdk import LMApi
from logicmonitor_sdk.configuration import Configuration
from logicmonitor_sdk.api.dashboard_group_api import DashboardGroupApi
from logicmonitor_sdk.api.dashboard_api import DashboardApi
from logicmonitor_sdk.exceptions import ApiException

# Set your API credentials
LM_ACCOUNT = "your-account-name"  # e.g. 'company123'
LM_ACCESS_ID = "your-access-id"
LM_ACCESS_KEY = "your-access-key"

# Setup configuration
config = Configuration(
    access_id=LM_ACCESS_ID,
    access_key=LM_ACCESS_KEY,
    account=LM_ACCOUNT
)

# Create API clients
lm = LMApi(configuration=config)
dashboard_api = DashboardApi(lm)
dashboard_group_api = DashboardGroupApi(lm)

# Output folder for backups
backup_folder = "dashboard_backups"
os.makedirs(backup_folder, exist_ok=True)

# Get all dashboard groups
try:
    dashboard_groups = dashboard_group_api.get_dashboard_group_list(size=1000).items
except ApiException as e:
    print(f"Error fetching dashboard groups: {e}")
    exit(1)

# Loop through all groups and their dashboards
for group in dashboard_groups:
    group_id = group.id
    group_name = group.name.replace("/", "_")
    
    try:
        dashboards = dashboard_api.get_dashboards_by_group_id(group_id=group_id).items
    except ApiException as e:
        print(f"Error fetching dashboards for group '{group_name}': {e}")
        continue

    for dashboard in dashboards:
        dashboard_id = dashboard.id
        dashboard_name = dashboard.name.replace("/", "_")
        
        try:
            # Get full dashboard config
            dashboard_detail = dashboard_api.get_dashboard_by_id(dashboard_id)
            file_path = os.path.join(
                backup_folder,
                f"{group_name}__{dashboard_name}_{dashboard_id}.json"
            )
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(dashboard_detail.to_dict(), f, indent=2)
            print(f"✔️ Backed up: {dashboard_name} (Group: {group_name})")
        except ApiException as e:
            print(f"❌ Failed to fetch or save dashboard {dashboard_name}: {e}")
