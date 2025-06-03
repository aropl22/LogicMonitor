'''
This Python script compares two CSV files based on the "CI Name" column and generates a new CSV file based on file1.csv. It adds a new column at the beginning of each row titled "In File2", which indicates whether the CI Name from file1.csv also exists in file2.csv.

Functionality
For each row in file1.csv, the script checks if the value in the "CI Name" column is also found in file2.csv.
If the CI Name exists in both files, it writes "YES" in the "In File2" column.

If the CI Name does not exist in file2.csv, the column is left blank.

All other fields from file1.csv remain unchanged.
'''

import csv

file1 = 'file1.csv'
file2 = 'file2.csv'
output_file = 'file1_with_flag.csv'
key_column = 'CI Name'

# Step 1: Load CI Names from file2 into a set for quick lookup
with open(file2, mode='r', newline='') as f2:
    reader2 = csv.DictReader(f2)
    ci_names_file2 = {row[key_column] for row in reader2}

# Step 2: Read file1 and write output with new column "In File2"
with open(file1, mode='r', newline='') as f1, open(output_file, mode='w', newline='') as fout:
    reader1 = csv.DictReader(f1)
    fieldnames = ['In File2'] + reader1.fieldnames  # Add new column at the beginning
    writer = csv.DictWriter(fout, fieldnames=fieldnames)
    writer.writeheader()

    for row in reader1:
        ci_name = row[key_column]
        in_both = 'YES' if ci_name in ci_names_file2 else ''
        output_row = {'In File2': in_both}
        output_row.update(row)
        writer.writerow(output_row)

print(f"Comparison complete. Output saved to: {output_file}")
