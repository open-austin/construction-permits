#  todo:
#  use dictwriter to write data
#  check for year folder and create it if not exists
#  inconsistent quotes usage

import arrow
import time
import requests
import geocoder
import logging
import csv
import pdb

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

#  debugging vars
bill = []

def get_data(start_date, end_date):
    start = start_date.format('MM/DD/YYYY')
    end = end_date.format('MM/DD/YYYY')
    print('Getting data from {} to {}'.format(start, end))
    data = {'sDate': start, 'eDate': end, 'Submit': 'Submit'}
    res = requests.post('http://www.austintexas.gov/oss_permits/permit_report.cfm', data=data)
    print(res.status_code, res.request.url)

    return res.content

def parse_table_html(data):
    data = str(data)
    data = data.replace("\\n","")
    data = data.replace("\\t","")
    data = data.replace("b'","")
    data = data.replace("<table border=\"1\">","")
    data = data.replace("</table>","")
    data = data.replace("<th>","")
    data = data.replace("</th>","|")
    data = data.replace("<td>","")
    data = data.replace("</td>",delim)
    data = data.replace("<tr>","")
    data = data.replace("</tr>","\n")
    return data
    
def geocode_data(data):
    reader = csv.DictReader(data.split('\n'),  delimiter='|')
    counter = 0
    #  create list of unique addresses 
    for row in reader:
        address = row['permit_location']
         
        if type(address) == str: #  normalize addresses and skip empty address fields
                address = address.upper().strip()
        else:
            continue #  data with invalid address is skipped

        if address not in address_dict:
            if counter < 2: #  only geocode a few records (dev only)
                print("hey!")
                counter =  counter + 1
                time.sleep(.5) #  delay for .5 seconds between lookup requests. the api limit is 5 requests per second
                found_address = geocoder.google(address +', Austin, TX')
                address_dict[address] = found_address
        
        if address in address_dict:
            if address_dict[address].lat:
                row['lat'] = address_dict[address].lat
                row['lng'] = address_dict[address].lng
                row['accuracy'] = address_dict[address].accuracy
                row["city"] = address_dict[address].city
                row["county"] = address_dict[address].county
                row["state"] = address_dict[address].state
                row["postal_code"] = address_dict[address].postal
        
        pdb.set_trace()        
        return data

def write_data(start_date, end_date, data):
    fname = 'data/{}/permit_report_{}_{}.xls'.format(start_date.format('YYYY'), start_date.format('MM-DD-YY'), end_date.format('MM-DD-YY'))
    print('Writing data from {} to {}'.format(start_date.format('MM/DD/YYYY'), end_date.format('MM/DD/YYYY')))
    with open(fname, 'w+') as fh:
        fh.write(data)

def main(start, end):
    delta = end - start
    days = delta.days + 1
    print('Fetching permit reports for {} days'.format(days))
    for day_number in range(0, days, interval):
        start_date = start.replace(days=day_number)
        end_date = start.replace(days=day_number+interval-1)
        data = get_data(start_date, end_date)
        data = parse_table_html(data)
        data = geocode_data(data)
        write_data(start_date, end_date, data)
    
delim = "|"
start = arrow.get(2015,12,7) #  (YYYY,M,D)
end = arrow.get(2015,12,7)
interval = 1 #  download, geocode, and write one day at a time
address_dict = dict()
main(start, end)
