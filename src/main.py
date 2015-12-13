# todo:
# throw out matches that match citycenter
# extra column before geocoded fields
# argparser for start_date, end_date

import logging
import time

import arrow
import geocoder
import requests
import pandas as pd

ADDRESS_CACHE = {}

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger('requests.packages.urllib3')
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True


def fetch_permits(date):
    print('Getting data for {}'.format(date, date))

    data = {'sDate': date, 'eDate': date, 'Submit': 'Submit'}
    res = requests.post('http://www.austintexas.gov/oss_permits/permit_report.cfm', data=data)

    print(res.status_code, res.request.url)
    if not res.ok:
        print(res.headers)
        print(res.content)
    res.raise_for_status()

    return res.content


def parse_permits(data):
    dataframes = pd.read_html(data)[0]
    dataframes = geocode_data(dataframes)
    return dataframes.to_csv(index=False, header=False)


def geocode_data(data):
    # geocoded_data = []
    #  create list of unique addresses
    import ipdb; ipdb.set_trace()
    # for row in reader:
    #     address = row['permit_location']
    #     if type(address) == str:  # normalize addresses and skip empty address fields
    #             address = address.upper().strip()
    #     else:
    #         continue  # data with invalid address is skipped
    #
    #     if address not in ADDRESS_CACHE:
    #         time.sleep(.5)  # delay for .5 seconds between lookup requests. the api limit is 5 requests per second
    #         found_address = geocoder.google(address + ', Austin, TX')
    #         ADDRESS_CACHE[address] = found_address
    #
    #     if address in ADDRESS_CACHE:
    #         if ADDRESS_CACHE[address].lat:
    #             row['lat'] = ADDRESS_CACHE[address].lat
    #             row['lng'] = ADDRESS_CACHE[address].lng
    #             row['accuracy'] = ADDRESS_CACHE[address].accuracy
    #             row['city'] = ADDRESS_CACHE[address].city
    #             row['county'] = ADDRESS_CACHE[address].county
    #             row['state'] = ADDRESS_CACHE[address].state
    #             row['postal_code'] = ADDRESS_CACHE[address].postal
    #
    #     geocoded_data.append(row)
    # print(str(len(ADDRESS_CACHE)) + ' unique addresses geocoded')
    # return (geocoded_data, fieldnames)


def write_permits(date, permits_csv):
    fname = 'data/permit_report_{}_{}.xls'.format(date.format('YYYY'), date.format('MM-DD-YY'))
    print('Writing data to {}'.format(fname))

    with open(fname, 'w+') as fh:
        fh.write(permits_csv)


def store_permits_for_date(date):
    print('Fetching permit reports for {}'.format(date))
    try:
        data = fetch_permits(date)
        permits_csv = parse_permits(data)
        write_permits(date, permits_csv)
    except Exception as e:
        print('Failed to get data for {}'.format(date))
        print(e)


if __name__ == '__main__':
    today = arrow.now().format('MM-DD-YYYY')
    store_permits_for_date(today)
