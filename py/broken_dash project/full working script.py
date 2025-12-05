import csv

# ---------------------
# INPUT: your dictionary
# ---------------------
data = report  # rename for clarity


# =============================
# CSV 1: dashboards.csv
# =============================
with open("dashboards.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["group_name", "dashboard_name", "dashboard_id", "widget_tokens"])

    for group_name, group_data in data.get("groups", {}).items():
        for dash_id, dash_info in group_data.get("dashboards", {}).items():

            tokens = dash_info.get("widget_tokens")
            token_str = ", ".join(tokens) if tokens else "NONE"

            writer.writerow([
                group_name,
                dash_info.get("name", "UNKNOWN"),
                dash_id,
                token_str
            ])


# =============================
# CSV 2: missing_widget_tokens.csv
# =============================
with open("missing_widget_tokens.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["group_name", "dashboard_name", "dashboard_id"])

    for group_name, group_data in data.get("groups", {}).items():
        for dash_id, dash_info in group_data.get("dashboards", {}).items():
            if not dash_info.get("widget_tokens"):
                writer.writerow([
                    group_name,
                    dash_info.get("name", "UNKNOWN"),
                    dash_id
                ])


# =============================
# CSV 3: broken_widgets.csv
# (widgets missing required fields)
# =============================
with open("broken_widgets.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["widget_token", "missing_fields"])

    for token, widget_info in data.get("widgets", {}).items():

        # define required fields
        required = ["name", "type"]

        missing = [field for field in required if field not in widget_info]

        if missing:
            writer.writerow([token, ", ".join(missing)])


print("CSV files generated:")
print(" - dashboards.csv")
print(" - missing_widget_tokens.csv")
print(" - broken_widgets.csv")
