import arrow
import requests

import logging
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True


def get_data(start_date, end_date):
    start = start_date.format('MM/DD/YYYY')
    end = end_date.format('MM/DD/YYYY')
    print('Getting data from {} to {}'.format(start, end))
    data = {'sDate': start, 'eDate': end, 'Submit': 'Submit'}
    res = requests.post('http://www.austintexas.gov/oss_permits/permit_report.cfm', data=data)
    print(res.status_code, res.request.url)
    if not res.ok:
        print(res.headers)
        print(res.content)
    res.raise_for_status()

    return res.content


def write_data(start_date, end_date, data):
    fname = 'data/permit_report_{}_{}.xls'.format(start_date.format('MM-DD-YY'), end_date.format('MM-DD-YY'))
    print('Writing data to {}'.format(fname))
    with open(fname, 'w+') as fh:
        fh.write(data)


def main(start, end):
    delta = end - start
    days = delta.days + 2
    print('Fetching permit reports for {} days'.format(days))
    for day_number in range(days):
        start_date = end_date = start.replace(days=day_number)
        try:
            data = get_data(start_date, end_date)
            write_data(start_date, end_date, data)
        except Exception as e:
            print('Failed to get data for {} to {}'.format(start_date, end_date))
            print(e)


start = arrow.get('01-01-2015')
end = arrow.now()
main(start, end)
