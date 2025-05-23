# 🛡️ LogicMonitor Dashboard Backup Script
This Python script retrieves and lists all devices in a specified device group from your LogicMonitor account using using the [LogicMonitor SDK v3](https://pypi.org/project/logicmonitor-sdk/). 
It handles API pagination to fetch all devices and prints their ID, display name, and IP address.

---

## 📦 Features

Authenticates using credentials from a JSON file
Loads configuration (device group name) from config.json
Retrieves the device group ID by name
Fetches all devices in the group with pagination support
Prints each device's ID, name, and primary IP address
Gracefully handles API exceptions

---

## 🔧 Requirements

- Python 3.7+
- `logicmonitor-sdk` v3

Install the SDK:
```bash
pip install logicmonitor-sdk
```

🚀 Usage
Create a credentials.json file in the same directory as the script with the following format:

```json
{
  "account": "your-account-name",
  "access_id": "your-access-id",
  "access_key": "your-access-key"
}
```
Create a config.json file specifying the device group to query:

```json
{
  "group_name": "Your Device Group Name"
}
```
Run the script:

```bash
python main.py
```

Output Example:

```sql
Group Name: Your Device Group Name
Group ID: 12345

Device list: 

101 - DeviceOne - 192.168.1.10
102 - DeviceTwo - 192.168.1.11
...
```
