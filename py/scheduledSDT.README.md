🕒 LogicMonitor Scheduled Downtime (SDT) Script
This PowerShell script automates the process of adding Scheduled Downtime (SDT) for LogicMonitor devices listed in a CSV file. Script parameters like comment, start/end time, and file paths are dynamically loaded from a sdt_params.json configuration file.

📦 Features

Adds SDTs to LogicMonitor devices from a CSV file
Parameters loaded dynamically from a JSON file
Logs output messages to both the console and a time-stamped log file
Handles errors gracefully with detailed logs

🔧 Requirements

Windows PowerShell 5.1 or PowerShell 7+

LogicMonitor PowerShell module installed (Install-Module LogicMonitor)
API credentials configured for the current PowerShell session or context

🗂️ Input Files
sdt_params.json
Create this file in the same directory as the script with the following format:

```json
{
  "comment": "CHGxxxxxxx - Scheduled Maintenance Window",
  "startDate": "YYYY-MM-DD HH:MM AM/PM",
  "endDate": "YYYY-MM-DD HH:MM AM/PM",
  "csvFileName": "sdt_hosts.csv"
}
```

sdt_hosts.csv
Example content (must include a DeviceName column):

```csv

DeviceName
server01
server02
router1
```

🚀 Usage

Make sure the required files (sdt_params.json, your CSV file) are in the same directory as the script.
Open a PowerShell terminal in that directory.

Run the script:

```powershell

.\bulk_SDT.ps1
```

A log file will be created with a name like:

```bash
sdt_log_20250523151230.log
```
All events are printed to both the terminal and the log file.

✅ Output

Each SDT attempt will be logged as either:

SUCCESS: Added SDT for device: <DeviceName>
ERROR: Could not add SDT for device: <DeviceName>
ERROR: Exception for device: <DeviceName> - <ErrorMessage>