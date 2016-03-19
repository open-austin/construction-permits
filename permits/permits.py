#!/usr/bin/env python
# -*- coding: utf-8 -*-

# todo:
# throw out matches that match citycenter
# extra column before geocoded fields
# argparser for start_date, end_date

import csv
import logging
from StringIO import StringIO

import arrow
import requests

import geocode
import github
from html2csv import html2csv
import secrets


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

    file = StringIO(csv_text)
    reader = csv.DictReader(file)

    return reader


def parse_permits(reader):
    rows = []

    for row in reader:
        address = geocode.geocode_address(row['permit_location'])
        if address and address.get('lat'):
            row.update(address)

        rows.append(row)
    return rows



def write_permits_file(filename, rows, fieldnames):
    with open(filename, 'w+') as fh:
        print('Writing data to file {}'.format(filename))
        write_permits(fh, rows, fieldnames)


def write_permits_github(filename, rows, fieldnames):
    fh = StringIO()
    write_permits(fh, rows, fieldnames)
    csv_text = StringIO.getvalue(fh)
    github.create_or_update_file(filename, 'master', csv_text, 'Automated commit {}'.format(filename))


def write_permits(file, rows, fieldnames):
    writer = csv.DictWriter(file, fieldnames, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)


def store_permits_for_date(date, in_lambda=False):
    print('Fetching permit reports for {}'.format(date))
    try:
        html = fetch_permits(date)
        reader = parse_html(html)
        rows = parse_permits(reader)

        filename = 'data/{}/{}.csv'.format(date.format('YYYY'), date.format('YYYY-MM-DD'))
        fieldnames = reader.fieldnames + ['geocoded_address', 'geocoder', 'lat', 'lng', 'accuracy', 'city', 'postal_code', 'state', 'county']

        if not in_lambda:
            write_permits_file(filename, rows, fieldnames)
        write_permits_github(filename, rows, fieldnames)
    except Exception as e:
        print('Failed to get data for {}'.format(date))
        print(e)
        raise e


def lambda_handler(event, context):
    today = arrow.now('America/Chicago')
    store_permits_for_date(today, in_lambda=True)


if __name__ == '__main__':
    today = arrow.now('America/Chicago')
    store_permits_for_date(today, in_lambda=False)
