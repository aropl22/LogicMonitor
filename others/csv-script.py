'''
Script Description
This Python script compares two CSV files based on the "CI Name" column. It identifies which CI Names appear in one file but are missing from the other, and generates a third CSV file listing all such missing CI Names. The output CSV contains only the "CI Name" column, providing a concise view of differences between the two datasets.

Use cases:
Quickly find configuration items that exist in one source but not another.
Validate synchronization between two inventories or CMDB exports.
Track missing or new items during data reconciliation.

Inputs:
file1.csv — first CSV file containing a "CI Name" column.
file2.csv — second CSV file containing a "CI Name" column.

Output:
ci_name_differences.csv — CSV file listing all CI Names missing from either file.
'''

import csv

file1 = 'file1.csv'
file2 = 'file2.csv'
output_file = 'ci_name_differences.csv'
key_column = 'CI Name'

def get_ci_names(filename):
    with open(filename, mode='r', newline='') as f:
        reader = csv.DictReader(f)
        return {row[key_column] for row in reader}

# Get unique CI Names from both files
ci_names_file1 = get_ci_names(file1)
ci_names_file2 = get_ci_names(file2)

# Find CI Names missing from each
only_in_file1 = ci_names_file1 - ci_names_file2
only_in_file2 = ci_names_file2 - ci_names_file1

# Combine all differences
differences = sorted(only_in_file1.union(only_in_file2))

# Write to output CSV
with open(output_file, mode='w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([key_column])  # header
    for ci_name in differences:
        writer.writerow([ci_name])

print(f"Done. Differences written to: {output_file}")
