import os
import csv

address_file = open('unique_addresses_XY.csv', 'r')
address_reader = csv.DictReader(address_file)
address_data = list(address_reader)
address_file.close()

for root, dirs, files in os.walk('.'):
    for name in files:
        if ('.csv' in name):
            if ('Y.csv' not in name):  # ignore unique_addresses_XY.csv
                current_file = os.path.join(root, name)
                with open(current_file, 'r') as inputfile:
                    reader = csv.DictReader(inputfile)
                    outfile = open(os.path.join(root,
                                                'new_' + name), 'w')
                    fieldnames = reader.fieldnames
                    fieldnames = fieldnames + ['lat'] + ['lon']
                    writer = csv.DictWriter(outfile,
                                            fieldnames=fieldnames,
                                            delimiter=',',
                                            lineterminator='\n')
                    writer.writeheader()
                    for row in reader:
                        lookup = row['permit_location']
                        for address in address_data:
                            if lookup == address['original']:
                                lat = address['lat']
                                lon = address['lon']
                                row['lat'] = lat
                                row['lon'] = lon
                                break
                        writer.writerow(row)
                    outfile.close()
