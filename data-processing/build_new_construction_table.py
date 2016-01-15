#  read a csv of permit data and build a csv of new construction permits only

import csv

fieldnames = []

with open("master_permit_data.csv", 'r') as inputfile:
    with open("new_construction_data.csv", 'w') as outfile:
        reader = csv.DictReader(inputfile)
        fieldnames = reader.fieldnames
        writer = csv.DictWriter(outfile,fieldnames=fieldnames,lineterminator='\n')
        writer.writeheader()
        for row in reader:
            if "BP" in row['permit_number']:
                if "NEW" in row['work_type'].upper():
                        writer.writerow(row)
