import csv
import platform
import subprocess

# Input CSV file with a column "Device" (IP or hostname)
input_file = "devices.csv"
output_file = "devices_with_ping.csv"

# Determine ping command based on OS
param = "-n" if platform.system().lower() == "windows" else "-c"

# Read CSV and ping devices
with open(input_file, newline='') as csvfile:
    reader = list(csv.DictReader(csvfile))
    fieldnames = reader[0].keys() | {"Ping Result"}  # add new column
    
    for row in reader:
        device = row["Device"]
        try:
            result = subprocess.run(
                ["ping", param, "1", device],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            row["Ping Result"] = "Reachable" if result.returncode == 0 else "Unreachable"
        except Exception as e:
            row["Ping Result"] = f"Error: {e}"

# Write new CSV with ping results
with open(output_file, "w", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(reader)

print(f"Ping results saved to {output_file}")