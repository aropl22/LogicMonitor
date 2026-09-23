# LogicMonitor Dashboard Update Script

## Overview

This Python script automates the process of importing and updating LogicMonitor dashboards from a local directory.

The dashboard JSON files are downloaded separately using the **GitHub Dashboard Download Script**. The Dashboard Update Script does **not** download dashboards from GitHub.

Before making any changes, the script prompts the user to confirm that a backup of the existing LogicMonitor dashboard configuration has already been created.

The script then processes the local dashboard JSON files, creates missing dashboard groups and dashboards, and updates existing dashboards while preserving the dashboard folder hierarchy.

---

## Features

* Processes dashboard JSON files from the local `lm-dashboards` directory
* Creates missing LogicMonitor dashboard groups
* Creates dashboards that do not already exist
* Updates existing dashboards
* Preserves the local dashboard folder hierarchy in LogicMonitor
* Does not delete existing dashboards
* Prompts the user to confirm that a backup has been created before making changes
* Uses the LogicMonitor Python SDK
* Handles LogicMonitor API rate limits
* Creates timestamped log files
* Reports dashboard creation, updates, and errors

---

## Requirements

* Python 3.x
* LogicMonitor Python SDK
* Valid LogicMonitor API credentials
* Appropriate LogicMonitor permissions to create and update dashboards and dashboard groups
* Dashboard JSON files in the `lm-dashboards` directory
* A backup of the existing LogicMonitor dashboard configuration created separately before running the script

---

## Directory Structure

A typical working directory looks like:

```text
lm-dashboard-update/
│
├── dashboard_update.py
│
├── config/
│   ├── sandbox_config.json
│   └── production_config.json
│
├── lm-dashboards/
│   └── ...
│
└── logs/
    └── YYYYMMDD_HHMMSS.log
```

### `dashboard_update.py`

Main script responsible for processing the local dashboard JSON files and creating or updating dashboards in LogicMonitor.

### `config/`

Contains environment-specific LogicMonitor configuration files.

Example:

```text
config/
├── sandbox_config.json
└── production_config.json
```

### `lm-dashboards/`

Contains the dashboard JSON files that will be imported or updated.

The folder structure is used to determine the LogicMonitor dashboard group hierarchy.

Example:

```text
lm-dashboards/
├── Network/
│   ├── Cisco/
│   │   └── Network Overview.json
│   └── Routing/
│       └── BGP Overview.json
│
├── Servers/
│   ├── Windows/
│   │   └── Windows Overview.json
│   └── Linux/
│       └── Linux Overview.json
│
└── Storage/
    └── Storage Overview.json
```

### `logs/`

Contains timestamped log files generated during script execution.

Example:

```text
logs/
└── 20260923_103000.log
```

---

## Dashboard Download

Dashboard files are downloaded separately using the **GitHub Dashboard Download Script**.

The Dashboard Update Script does not connect to GitHub or download dashboard files.

The normal workflow is:

```text
GitHub
   |
   v
GitHub Dashboard Download Script
   |
   v
lm-dashboards/
   |
   v
Dashboard Update Script
   |
   v
LogicMonitor
```

The separation allows the downloaded dashboard files to be reviewed before making changes to LogicMonitor.

---

## LogicMonitor Dashboard Group

Dashboards are imported under the designated root dashboard group:

```text
LogicMonitor Dashboards imported
```

The local directory structure is used to create the corresponding LogicMonitor dashboard group hierarchy.

For example:

```text
lm-dashboards/Network/Cisco/Network Overview.json
```

is mapped to:

```text
LogicMonitor Dashboards imported
└── Network
    └── Cisco
        └── Network Overview
```

If a required dashboard group does not exist, the script creates it.

---

## Backup Confirmation

The Dashboard Update Script does **not create the backup**.

A backup of the existing LogicMonitor dashboard configuration must be created separately before running the script.

When the script starts processing the update, it prompts the user to confirm that the backup has already been created.

Example:

```text
Has the dashboard backup been created? (Y/N):
```

Enter:

```text
Y
```

to continue.

Enter:

```text
N
```

to stop the script.

The script will not proceed with dashboard changes unless the backup is confirmed.

---

## Configuration

The script uses environment-specific configuration files to connect to LogicMonitor.

Example:

```json
{
    "company": "YOUR_LM_COMPANY",
    "access_id": "YOUR_ACCESS_ID",
    "access_key": "YOUR_ACCESS_KEY"
}
```

Configuration files should contain the appropriate credentials for the LogicMonitor environment being updated.

**Do not commit API credentials or access keys to source control.**

---

## Dashboard Processing

After the backup is confirmed, the script recursively scans the:

```text
./lm-dashboards
```

directory.

For each dashboard JSON file, the script determines:

* Dashboard name
* Local folder path
* Corresponding LogicMonitor dashboard group
* Whether the dashboard already exists

The relative folder structure determines the destination dashboard group.

---

## Create and Update Behavior

The script supports both dashboard creation and dashboard updates.

### Existing Dashboard

If the dashboard already exists in the target LogicMonitor group, the script updates the existing dashboard.

### Missing Dashboard

If the dashboard does not exist, the script creates the dashboard.

### Missing Dashboard Group

If the required dashboard group does not exist, the script creates the group before processing the dashboard.

---

## Dashboard Deletion

The script does **not delete dashboards**.

If a dashboard exists in LogicMonitor but is not present in the local `lm-dashboards` directory, it will not be automatically removed.

This prevents dashboards from being accidentally deleted during the update process.

---

## Logging

The script creates timestamped log files in the `logs` directory.

Example:

```text
logs/
└── 20260923_103000.log
```

The log records the dashboard update process and can be used for troubleshooting and auditing.

Information recorded may include:

* Dashboard being processed
* Dashboard group being processed
* Dashboard creation
* Dashboard updates
* Dashboard group creation
* Errors
* API-related issues
* Processing results

---

## API Rate Limiting

The script uses the LogicMonitor Python SDK to communicate with the LogicMonitor API.

LogicMonitor API requests are subject to rate limits.

The script includes handling for API rate-limit responses and waits before continuing when necessary.

The applicable API limit is:

```text
500 requests / 60 seconds
```

If rate limiting occurs, allow the script's wait/retry process to complete.

Avoid running multiple copies of the script simultaneously.

---

## Running the Script

### Step 1 — Download Dashboards

Run the separate **GitHub Dashboard Download Script**.

Verify that the expected dashboard JSON files are present in:

```text
./lm-dashboards
```

### Step 2 — Review Dashboard Files

Review the downloaded dashboard files and directory structure before making changes to LogicMonitor.

### Step 3 — Create the Backup

Create a backup of the existing LogicMonitor dashboard configuration using the appropriate backup process.

The Dashboard Update Script does not create this backup.

### Step 4 — Run the Script

Run:

```bash
python dashboard_update.py
```

### Step 5 — Confirm the Backup

When prompted:

```text
Has the dashboard backup been created? (Y/N):
```

Enter:

```text
Y
```

to continue.

Enter:

```text
N
```

to stop.

### Step 6 — Review the Results

After the script completes:

* Review the log file in the `logs` directory
* Check for errors
* Verify newly created dashboards
* Verify updated dashboards
* Confirm the dashboard hierarchy in LogicMonitor

---

## Recommended Workflow

The recommended process is:

1. Run the **GitHub Dashboard Download Script**
2. Review the downloaded dashboard JSON files
3. Verify the `lm-dashboards` directory structure
4. Create a backup of the existing LogicMonitor dashboard configuration
5. Run the **Dashboard Update Script**
6. Confirm that the backup was created
7. Allow the script to process the dashboards
8. Review the execution log
9. Verify the dashboards in LogicMonitor

---

## Troubleshooting

### Dashboard Is Not Created

Check:

* The dashboard JSON file exists in `lm-dashboards`
* The JSON file is valid
* The required dashboard group exists or can be created
* The API credentials are valid
* The API account has sufficient permissions
* The execution log for the specific error

### Existing Dashboard Is Not Updated

Check:

* Dashboard name
* Dashboard ID
* Dashboard group ID
* Dashboard hierarchy
* Dashboard JSON contents
* LogicMonitor API response
* Execution log

### Incorrect Dashboard Group

The destination group is determined by the local directory structure.

Verify that the directory structure under:

```text
lm-dashboards/
```

matches the desired LogicMonitor dashboard hierarchy.

### API Rate Limit

If the LogicMonitor API rate limit is reached:

* Allow the script to wait and retry
* Avoid running multiple copies of the script
* Review the execution log
* Check for unnecessary API calls

---

## Security

Protect all LogicMonitor API credentials.

Do not:

* Commit credentials to GitHub
* Store credentials directly in the Python source code
* Include API keys in the README
* Share production configuration files containing credentials

Use appropriate permissions for configuration files and API accounts.

---

## Components

| Component             | Purpose                                           |
| --------------------- | ------------------------------------------------- |
| `dashboard_update.py` | Main LogicMonitor dashboard create/update process |
| `lm-dashboards/`      | Local dashboard JSON files                        |
| `logs/`               | Timestamped execution logs                        |
| `auth_sdk`            | Authentication module                             |
| `backup_message.py`   | Helper module, displays backup message            |
| `folder_trees.py/`    | Helper module, handles folder hierarchy           |
| `map_data.py`         | Helper module, maps data used during processing   |
| `script_logging.py/`  | Helper module, records script activity to log file|
| `updates.py`          | Helper module, creating and updating LM dashboards|


The **GitHub Dashboard Download Script** and the **dashboard backup process** are separate from the Dashboard Update Script.

---

## Summary

The LogicMonitor Dashboard Update Script provides a controlled process for importing and updating dashboards from a local set of dashboard JSON files.

The script:

* Processes local dashboard JSON files
* Preserves the dashboard folder hierarchy
* Creates missing dashboard groups
* Creates missing dashboards
* Updates existing dashboards
* Does not delete existing dashboards
* Requires confirmation that a backup was created before making changes
* Handles LogicMonitor API rate limits
* Maintains timestamped execution logs

The dashboard download and backup processes are intentionally separate from the Dashboard Update Script.
