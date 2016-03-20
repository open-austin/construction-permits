import json
import os
import mock
import unittest

from permits.permits import parse_permits
from permits.permits import parse_html
from permits.permits import write_permits_github

def mock_city_name_for_point(lng, lat):
    return 'mock austin'


def mock_zipcode_for_point(lng, lat):
    return 'mock zip'


def mock_query_address_geocoder(permit_location):
    # return None for roughly 1/3 of geocode attempts
    h = sum([ord(c) for c in permit_location])
    if (h % 3) == 0:
        return {
            u'candidates': [
                {
                    u'address': u'not the best',
                    u'attributes': {},
                    u'location': {
                        u'x': 3114989.499799113,
                        u'y': 10213624.997799426
                    },
                    u'score': 65.4
                },
                {
                    u'address': u'coa_address address',
                    u'attributes': {},
                    u'location': {
                        u'x': 3124989.499799113,
                        u'y': 10113624.997799426
                    },
                    u'score': 100
                },
                {
                    u'address': u'also not best',
                    u'attributes': {},
                    u'location': {
                        u'x': 3024989.499799113,
                        u'y': 12113624.997799426
                    },
                    u'score': 99
                },
            ],
            u'spatialReference': {u'latestWkid': 2277, u'wkid': 102739}
        }


def mock_query_coa_feature_server(permit_location):
    # return None for roughly 1/3 of geocode attempts
    h = sum([ord(c) for c in permit_location])
    if (h % 3) == 1:
        return {
            u'crs': {
                u'properties': {
                    u'name': u'EPSG:4326'
                },
                u'type': u'name'
            },
            u'features': [
                {
                    u'geometry': {
                        u'coordinates': ['lng', 'lat'],
                        u'type': u'Point'
                    },
                    u'id': 717800,
                    u'properties': {
                        u'ADDRESS': 10803,
                        u'ADDRESS_FRACTION': None,
                        u'ADDRESS_SUFFIX': None,
                        u'ADDRESS_TYPE': 1,
                        u'CREATED_BY': u'GIS-library',
                        u'CREATED_DATE': 943920000000,
                        u'FULL_STREET_NAME': u'coa address',
                        u'MODIFIED_BY': None,
                        u'MODIFIED_DATE': 943920000000,
                        u'OBJECTID': 717800,
                        u'PARENT_PLACE_ID': 7970,
                        u'PLACE_ID': 401121,
                        u'PREFIX_DIRECTION': None,
                        u'PREFIX_TYPE': None,
                        u'SEGMENT_ID': 2010032,
                        u'STREET_NAME': u'TOPPERWEIN',
                        u'STREET_TYPE': u'DR',
                        u'SUFFIX_DIRECTION': None},
                        u'type': u'Feature'
                }
            ],
            u'type': u'FeatureCollection'
        }


class MockGeocoderAddress():
    def __init__(self):
        self.address = 'mapzen address'
        self.geocoder = 'mapzen geocoder'
        self.lat = 'mapzen lat'
        self.lng = 'mapzen lng'
        self.accuracy = 'mapzen accuracy'
        self.city = 'mapzen city'
        self.county = 'mapzen county'
        self.state = 'mapzen state'
        self.postal = 'mapzen postal'


def mock_geocoder(address, **kwargs):
    return MockGeocoderAddress()


class TestPermits(unittest.TestCase):

    def get_data_file(self, path):
        with open(os.path.join('tests', 'fixtures', path), 'r') as fh:
            return fh.read()

    @mock.patch('geocoder.mapzen', mock_geocoder)
    @mock.patch('permits.geocode._query_coa_geocoder', mock_query_address_geocoder)
    @mock.patch('permits.geocode._query_coa_feature_server', mock_query_coa_feature_server)
    @mock.patch('permits.geocode.city_name_for_point', mock_city_name_for_point)
    @mock.patch('permits.geocode.zipcode_for_point', mock_zipcode_for_point)
    @mock.patch('permits.geocode.SLEEP_TIME', 0)
    def test_parse_permits(self):
        permits_html = self.get_data_file('permits.html')
        reader = parse_html(permits_html)

        rows = parse_permits(reader)
        with open('out.json', 'wb') as f:
            f.write(json.dumps(rows))
        expected = json.loads(self.get_data_file('results.json'))
        self.assertEqual(expected, rows)

    def test_write_permits_github(self):
        with mock.patch('permits.github.create_or_update_file', mock.Mock()) as create_or_update_file:
            write_permits_github('wef', [{'A': 31, 'B': 52, 'C': 3}, {'A': 4}], ['A', 'B', 'C'])

        expected_args = [mock.call('wef', 'master', 'A,B,C\n31,52,3\n4,,\n', 'Automated commit wef', ('luqmaan', '07cfcee0eff4337dc251608bcd0553639cf5c405'))]
        self.assertEqual(expected_args, create_or_update_file.call_args_list)
