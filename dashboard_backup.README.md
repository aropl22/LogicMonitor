# 🛡️ LogicMonitor Dashboard Backup Script

This Python script backs up all dashboards from your LogicMonitor account using the [LogicMonitor SDK v3](https://pypi.org/project/logicmonitor-sdk/). 
Each dashboard is saved as a JSON file, organized by group and timestamped for easy tracking and recovery.

---

## 📦 Features

- Retrieves all dashboard groups and dashboards
- Saves each dashboard's full configuration as a `.json` file
- Outputs to a timestamped backup folder
- Gracefully handles API exceptions

---

## 🔧 Requirements

- Python 3.7+
- `logicmonitor-sdk` v3

Install the SDK:
```bash
pip install logicmonitor-sdk
```
## 🚀 Usage

Create a credentials.json file in the same directory as the script with the following format:

```json

{
  "account": "your-account-name",
  "access_id": "your-access-id",
  "access_key": "your-access-key"
}
```

Run the script:

```bash
python main.py
```
Backups will be saved in a folder like:

```bash
dashboard_backups/backup_2025-05-23_14-45-01/
```
Each file is named using this pattern:

```php-template
<GroupName>__<DashboardName>_<DashboardID>.json
```
