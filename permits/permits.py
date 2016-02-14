#!/usr/bin/env python
# -*- coding: utf-8 -*-

# todo:
# throw out matches that match citycenter
# extra column before geocoded fields
# argparser for start_date, end_date

import csv
import logging
from StringIO import StringIO
import time

import arrow
import attrdict
import geocoder
import requests

import github
from html2csv import html2csv
import secrets

ADDRESS_CACHE = {}
SLEEP_TIME = 0.2
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

    file = StringIO(csv_text)
    reader = csv.DictReader(file)

    return reader


def parse_permits(reader):
    rows = []

    for row in reader:
        address = geocode_address(row['permit_location'])
        if address and address.lat:
            row['geocoded_address'] = address.address
            row['geocoder'] = address.geocoder
            row['lat'] = address.lat
            row['lng'] = address.lng
            row['accuracy'] = address.accuracy
            row['city'] = address.city
            row['county'] = getattr(address, 'county', '')
            row['state'] = address.state
            row['postal_code'] = address.postal

        rows.append(row)
    return rows


def geocode_address(permit_location):
    if permit_location in ADDRESS_CACHE:
        return ADDRESS_CACHE[permit_location]
    if type(permit_location) is not str:
        return

    geocoded_address = geocode_from_coa_address_server(permit_location)
    if not geocoded_address:
        address = permit_location.upper().strip()
        for scrubber in SCRUBBERS:
            address = address.replace(scrubber, ' ')
        address = '{}, Austin, TX'.format(address)

        geocoded_address = geocoder.mapzen(address, key=secrets.MAPZEN_API_KEY)
        geocoded_address.geocoder = 'mapzen'
        ADDRESS_CACHE[permit_location] = geocoded_address
        time.sleep(SLEEP_TIME)

    return geocoded_address


def geocode_from_coa_address_server(permit_location):
    permit_location = permit_location.split('UNIT')[0]
    permit_location = permit_location.split('BLDG')[0]
    permit_location = permit_location.strip()
    url = "http://services.arcgis.com/0L95CJ0VTaxqcmED/ArcGIS/rest/services/LOCATION_address_point/FeatureServer/0/query"
    req = requests.get(url, {
        'where': "full_street_name LIKE '{permit_location}'".format(permit_location=permit_location),
        'outFields': '*',
        'returnGeometry': 'true',
        'outSR': '4326',
        'f': 'pgeojson',
    })
    feature = _get_single_feature_only(req)
    if feature:
        coordinates = feature.get('geometry').get('coordinates')
        city_name = city_name_for_point(*coordinates)
        zipcode = zipcode_for_point(*coordinates)
        props = feature.get('properties')
        return attrdict.AttrDefault(lambda : None, {
            'address': props.get('FULL_STREET_NAME'),
            'city': city_name,
            'geocoder': 'coa_addresses',
            'lat': coordinates[1],
            'lng': coordinates[0],
            'postal': zipcode,
            'state': 'Texas',
        })


def city_name_for_point(lng, lat):
    """returns city name for a given point, queried from CoA jurisdiction
    boundary data"""
    url = 'http://services.arcgis.com/0L95CJ0VTaxqcmED/ArcGIS/rest/services/BOUNDARIES_jurisdictions/FeatureServer/0/query'
    return _property_where_intersects(url, 'CITY_NAME', lng, lat)


def zipcode_for_point(lng, lat):
    """returns zipcode for a given point, queried from CoA zipcode boundary data"""
    url = 'http://services.arcgis.com/0L95CJ0VTaxqcmED/ArcGIS/rest/services/LOCATION_zipcodes/FeatureServer/0/query'
    return _property_where_intersects(url, 'ZIPCODE', lng, lat)


def _property_where_intersects(query_url, property_name, lng, lat):
    """queries for feature that intersects a given point, an returns the value
    of property_name at that point"""
    req = requests.get(query_url, {
        'geometry': '{lng},{lat}'.format(lng=lng, lat=lat),
        'geometryType': 'esriGeometryPoint',
        'inSR': '4326',
        'spatialRel': 'esriSpatialRelIntersects',
        'outFields': '*',
        'returnGeometry': 'false',
        'outSR': '4326',
        'f': 'pgeojson'
    })
    feature = _get_single_feature_only(req)
    if feature:
        return feature['properties'].get(property_name)
    else:
        return ''


def _get_single_feature_only(req):
    """returns feature from ArcGIS feature server geojson response only when
    there is a single feature in the response. Returns None if there are no
    features or more than one feature.
    """
    json_response = req.json()
    features = json_response.get('features')
    if features is not None and len(features) != 1:
        return
    else:
        return features[0]


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
