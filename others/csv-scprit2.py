import csv

file1 = 'file1.csv'
file2 = 'file2.csv'
output_file = 'file1_with_flag.csv'
key_column = 'CI Name'

# Load CI Names from file2 into a set
with open(file2, mode='r', newline='') as f2:
    reader2 = csv.DictReader(f2)
    ci_names_file2 = {row[key_column] for row in reader2}

# Open file1, read and write output with new column at the front
with open(file1, mode='r', newline='') as f1, open(output_file, mode='w', newline='') as fout:
    reader1 = csv.DictReader(f1)
    fieldnames = [ 'In File2' ] + reader1.fieldnames  # new column at front
    writer = csv.DictWriter(fout, fieldnames=fieldnames)
    writer.writeheader()

    for row in reader1:
        row_flag = 'YES' if row[key_column] in ci_names_file2 else ''
        # Insert new key-value pair at the front
        new_row = {'In File2': row_flag}
        new_row.update(row)
        writer.writerow(new_row)

print(f"Output written to {output_file}")
