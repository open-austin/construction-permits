#  walk through all the permit files and combine into one csv
#  run from same directory that contains /data/

import os
import csv

count = 0
fieldnames = []

with open("master_permit_data.csv", 'w') as outfile:
    for root, dirs, files in os.walk('.'):
        for name in files:
            if ('master' not in name):
                count += 1
                current_file = os.path.join(root, name)
                print(current_file)
                with open(current_file, 'r') as inputfile:
                    reader = csv.DictReader(inputfile)
                    if count == 1:
                        fieldnames = reader.fieldnames
                        writer = csv.DictWriter(outfile,fieldnames=fieldnames,lineterminator='\n')
                        writer.writeheader()
                    writer.writerows(row for row in reader)
