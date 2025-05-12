'''
Example usage: 

from csv_loader import load_csv_columns

csv_path = 'devices.csv'
columns_to_extract = ['Name', 'Start', 'End']  # You can change this list

try:
    data = load_csv_columns(csv_path, columns_to_extract)
    for row in data:
        print(row)
except ValueError as e:
    print(f"CSV column error: {e}")
'''

import csv

def load_csv_columns(file_path, required_columns):
    """
    Load specific columns from a CSV file.

    Args:
        file_path (str): Path to the CSV file.
        required_columns (list of str): List of column names to extract.

    Returns:
        list of dict: Each dict contains only the specified columns.
    """
    extracted_data = []

    with open(file_path, mode='r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        missing_cols = [col for col in required_columns if col not in reader.fieldnames]

        if missing_cols:
            raise ValueError(f"Missing columns in CSV: {missing_cols}")

        for row in reader:
            filtered_row = {col: row[col] for col in required_columns}
            extracted_data.append(filtered_row)

    return extracted_data