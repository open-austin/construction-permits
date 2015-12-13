#  todo:
#  inconsistent quotes usage
#  throw out matches that match citycenter
#  extra column before geocoded fields

import arrow
import os
import time
import requests
import geocoder
import logging
import csv

DELIM = '|'
address_dict = dict()

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger('requests.packages.urllib3')
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True


def get_data(today):
    print('Getting data from {} to {}'.format(today, today))
    data = {'sDate': today, 'eDate': today, 'Submit': 'Submit'}
    res = requests.post('http://www.austintexas.gov/oss_permits/permit_report.cfm', data=data)
    print(res.status_code, res.request.url)
    if not res.ok:
        print(res.headers)
        print(res.content)
    res.raise_for_status()
    return res.content


def parse_table_html(data):
    data = str(data)
    data = data.replace('\\n', '')
    data = data.replace('\\t', '')
    data = data.replace('b', '')
    data = data.replace('<table border="1">', '')
    data = data.replace('</table>', '')
    data = data.replace('<th>', '')
    data = data.replace('</th>', '|')
    data = data.replace('<td>', '')
    data = data.replace('</td>', DELIM)
    data = data.replace('<tr>', '')
    data = data.replace('</tr>', '\n')
    return data


def geocode_data(data):
    geocoded_data = []
    reader = csv.DictReader(data.split('\n'), delimiter=DELIM)
    fieldnames = reader.fieldnames + ['lat'] + ['lng'] + ['accuracy'] + ['city'] + ['postal_code'] + ['state'] + ['county']

    #  create list of unique addresses
    for row in reader:
        address = row['permit_location']
        if type(address) == str:  # normalize addresses and skip empty address fields
                address = address.upper().strip()
        else:
            continue  # data with invalid address is skipped

        if address not in address_dict:
            time.sleep(.5)  # delay for .5 seconds between lookup requests. the api limit is 5 requests per second
            found_address = geocoder.google(address + ', Austin, TX')
            address_dict[address] = found_address

        if address in address_dict:
            if address_dict[address].lat:
                row['lat'] = address_dict[address].lat
                row['lng'] = address_dict[address].lng
                row['accuracy'] = address_dict[address].accuracy
                row['city'] = address_dict[address].city
                row['county'] = address_dict[address].county
                row['state'] = address_dict[address].state
                row['postal_code'] = address_dict[address].postal

        geocoded_data.append(row)
    print(str(len(address_dict)) + ' unique addresses geocoded')
    return (geocoded_data, fieldnames)


def write_data(data, fieldnames):
    year = arrow.now().format('YYYY')
    today = arrow.now().format('MM-DD-YY')
    fname = 'data/{}/permit_report_{}_{}.xls'.format(year, today, today)
    if not os.path.exists('data/' + year):
        os.makedirs('data/' + year)

    with open(fname, 'w+') as fh:
        writer = csv.DictWriter(fh, fieldnames, delimiter=DELIM, lineterminator='\n')
        writer.writeheader()
        writer.writerows(data)


def main(today):
    print('Fetching permit reports for {}'.format(today))
    data = get_data(today)
    data = parse_table_html(data)
    data = geocode_data(data)
    write_data(data[0], data[1])

if __name__ == '__main__':
    today = arrow.now().format('MM/DD/YYYY')
    main(today)
