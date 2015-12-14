#!/usr/bin/env python

# todo:
# throw out matches that match citycenter
# extra column before geocoded fields
# argparser for start_date, end_date

import csv
import logging
import StringIO
import time

import arrow
import geocoder
import requests

import github
from html2csv import html2csv
from secrets import GITHUB_AUTH


ADDRESS_CACHE = {}
SLEEP_TIME = 0.3
SCRUBBERS = [' EB', ' SB', ' NB', ' WB', 'SVRD', ' AKA ', ' aka ', 'Blk', 'Block of ', '\'', 'UNK ']

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger('requests.packages.urllib3')
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True


def fetch_permits(date):
    print('Getting data for {}'.format(date, date))

    data = {'sDate': date.format('MM/DD/YYYY'), 'eDate': date.format('MM/DD/YYYY'), 'Submit': 'Submit'}
    print(data)
    res = requests.post('http://www.austintexas.gov/oss_permits/permit_report.cfm', data=data)

    print(res.status_code, res.request.url)
    if not res.ok:
        print(res.headers)
        print(res.text)
    res.raise_for_status()

    return res.text


def parse_html(html):
    # We could use pandas for this, but then pandas is a dependency :(
    parser = html2csv()
    parser.feed(html)
    csv_text = parser.getCSV()

    file = StringIO.StringIO(csv_text)
    reader = csv.DictReader(file)

    return reader


def parse_permits(reader):
    rows = []
    reader = [row for row in reader]

    for row in reader:
        address = geocode_address(row['permit_location'])
        if address and address.lat:
            row['geocoded_address'] = address.address
            row['lat'] = address.lat
            row['lng'] = address.lng
            row['accuracy'] = address.accuracy
            row['city'] = address.city
            row['county'] = address.county
            row['state'] = address.state
            row['postal_code'] = address.postal

        rows.append(row)

    return rows


def geocode_address(permit_location):
    if permit_location in ADDRESS_CACHE:
        return ADDRESS_CACHE[permit_location]
    if type(permit_location) is not str:
        return

    address = permit_location.upper().strip()
    for scrubber in SCRUBBERS:
        address = address.replace(scrubber, ' ')
    address = '{}, Austin, TX'.format(address)

    geocoded_address = geocoder.google(address)
    ADDRESS_CACHE[permit_location] = geocoded_address
    time.sleep(SLEEP_TIME)

    return geocoded_address


def write_permits_file(filename, rows, fieldnames):
    with open(filename, 'w+') as fh:
        print('Writing data to file {}'.format(filename))
        write_permits(fh, rows, fieldnames)


def write_permits_github(filename, rows, fieldnames):
    fh = StringIO.StringIO()
    write_permits(fh, rows, fieldnames)
    csv_text = fh.read()
    github.create_file(filename, 'master', csv_text, 'Automated commit {}'.format(filename), GITHUB_AUTH)


def write_permits(file, rows, fieldnames):
    writer = csv.DictWriter(file, fieldnames)
    writer.writeheader()
    writer.writerows(rows)


def store_permits_for_date(date):
    print('Fetching permit reports for {}'.format(date))
    try:
        html = fetch_permits(date)
        reader = parse_html(html)
        rows = parse_permits(reader)
        filename = 'data/{}/{}.csv'.format(date.format('YYYY'), date.format('YYYY-MM-DD'))
        fieldnames = reader.fieldnames + ['geocoded_address', 'lat', 'lng', 'accuracy', 'city', 'postal_code', 'state', 'county']
        write_permits(filename, rows, fieldnames)
    except Exception as e:
        print('Failed to get data for {}'.format(date))
        print(e)
        raise e


def main():
    today = arrow.now().replace(days=-1)
    store_permits_for_date(today)


def handler(event, context):
    print(event)
    print(context)
    main()

if __name__ == '__main__':
    main()
