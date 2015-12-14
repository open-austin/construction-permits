import csv
import json
import os
import mock
import unittest

from permits.permits import parse_permits
from permits.permits import parse_html


class MockAddress():
    def __init__(self):
        self.address = 'address'
        self.lat = 'lat'
        self.lng = 'lng'
        self.accuracy = 'accuracy'
        self.city = 'city'
        self.county = 'county'
        self.state = 'state'
        self.postal = 'postal'


class TestPermits(unittest.TestCase):

    def get_data_file(self, path):
        with open(os.path.join('tests', 'fixtures', path), 'r') as fh:
            return fh.read()

    @mock.patch('geocoder.google', lambda x: MockAddress())
    @mock.patch('permits.permits.SLEEP_TIME', 0)
    def test_parse_permits(self):
        permits_html = self.get_data_file('permits.html')
        reader = parse_html(permits_html)

        rows = parse_permits(reader)

        expected = json.loads(self.get_data_file('results.json'))
        self.assertEqual(expected, rows)
