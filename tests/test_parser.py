import csv
import os
import unittest

from permits.html2csv import html2csv


class TestParser(unittest.TestCase):

    def get_data_file(self, path):
        with open(os.path.join('tests', 'fixtures', path), 'r') as fh:
            return fh.read()

    def test_html2csv(self):
        permits_html = self.get_data_file('permits.html')
        expected_csv = self.get_data_file('permits.csv')

        parser = html2csv()
        parser.feed(permits_html)
        permits_csv = parser.getCSV()

        self.assertEqual(expected_csv, permits_csv)
