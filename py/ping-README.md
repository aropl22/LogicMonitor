# Ping Sweep CSV Script

## Overview

This Python script performs a ping sweep using a list of devices (IP addresses or hostnames) provided in a CSV input file. It checks the reachability of each device and writes the results to a new CSV file for easy analysis.

This script is especially useful when validating device availability while working with network reports from monitoring tools such as NetMRI or LogicMonitor.

---

## Features

* Reads device list from a CSV file
* Supports both Windows and Linux/macOS (auto-detects ping syntax)
* Sends a single ICMP ping per device
* Outputs results to a new CSV file
* Adds a **"Ping Result"** column with:

  * `Reachable`
  * `Unreachable`
  * Error messages (if applicable)

---

## Requirements

* Python 3.x
* No external libraries required (uses built-in modules only)

---

## Input File Format

The script expects a CSV file named:

```
devices.csv
```

It must include a column named:

```
Device
```

### Example:

```
Device
192.168.1.1
192.168.1.10
google.com
```

---

## Output

The script generates a new file:

```
devices_results.csv
```

This file will include all original columns plus:

```
Ping Result
```

### Example Output:

```
Device,Ping Result
192.168.1.1,Reachable
192.168.1.10,Unreachable
google.com,Reachable
```

---

## How It Works

1. Reads the input CSV file
2. Detects the operating system:

   * Windows → uses `-n`
   * Linux/macOS → uses `-c`
3. Sends 1 ping to each device
4. Evaluates the return code:

   * `0` → Reachable
   * Non-zero → Unreachable
5. Writes results to a new CSV file

---

## Usage

1. Place your `devices.csv` file in the same directory as the script
2. Run the script:

```
python script_name.py
```

3. Check the output file:

```
devices_with_ping.csv
```

---

## Notes / Limitations

* Some devices may block ICMP (ping), resulting in false "Unreachable" results
* Only sends a single ping per device (can be modified if needed)
* Script assumes the "Device" column exists and is correctly formatted

---

## Possible Improvements

* Add parallel processing for faster scans
* Allow configurable ping count and timeout
* Add logging or summary statistics
* Support multiple input columns (e.g., hostname + IP)

---

## Author Notes

This script is helpful for quickly validating device reachability and cross-referencing data from network monitoring reports.
