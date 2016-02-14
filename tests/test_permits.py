import json
import os
import mock
import unittest

from permits.permits import parse_permits
from permits.permits import parse_html
from permits.permits import write_permits_github

def mock_geocode_from_coa_address_server(permit_location):
    # return None for roughly half of geocode attempts
    h = sum([ord(c) for c in permit_location])
    if h % 2:
        return
    return {
        'lng': 'lng',
        'lat': 'lat',
        'address': 'address',
        'geocoder': 'coa_addresses',
        'city': 'city',
        'postal': 'postal',
        'state': 'state',
    }


class MockGeocoderAddress():
    def __init__(self):
        self.address = 'address'
        self.geocoder = 'geocoder'
        self.lat = 'lat'
        self.lng = 'lng'
        self.accuracy = 'accuracy'
        self.city = 'city'
        self.county = 'county'
        self.state = 'state'
        self.postal = 'postal'


def mock_geocoder(address, **kwargs):
    return MockGeocoderAddress()


class TestPermits(unittest.TestCase):

    def get_data_file(self, path):
        with open(os.path.join('tests', 'fixtures', path), 'r') as fh:
            return fh.read()

    @mock.patch('geocoder.mapzen', mock_geocoder)
    @mock.patch('permits.permits.geocode_from_coa_address_server', mock_geocode_from_coa_address_server)
    @mock.patch('permits.permits.SLEEP_TIME', 0)
    def test_parse_permits(self):
        permits_html = self.get_data_file('permits.html')
        reader = parse_html(permits_html)

        rows = parse_permits(reader)
        expected = json.loads(self.get_data_file('results.json'))
        self.assertEqual(expected, rows)

    def test_write_permits_github(self):
        with mock.patch('permits.github.create_or_update_file', mock.Mock()) as create_or_update_file:
            write_permits_github('wef', [{'A': 31, 'B': 52, 'C': 3}, {'A': 4}], ['A', 'B', 'C'])

        expected_args = [mock.call('wef', 'master', 'A,B,C\n31,52,3\n4,,\n', 'Automated commit wef', ('luqmaan', '07cfcee0eff4337dc251608bcd0553639cf5c405'))]
        self.assertEqual(expected_args, create_or_update_file.call_args_list)
