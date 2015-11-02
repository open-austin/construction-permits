# todo:
#  else statement to fetch already-geocoded addresses
#  write to file
#  permit reports should follow folder structure of the repo
#  testing
#  inconsistent quotes usage
			
import arrow
import requests
import geocoder
import logging

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
    if not res.ok:
        print(res.headers)
        print(res.content)
    res.raise_for_status()

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
	bill.append(data[0:5000])
    return data
    
def geocode_data(data):
	address_list = []
	geocoder_results = []
	reader = csv.DictReader(data.split('\n'),  delimiter='|')
    for row in reader:
	    address = row.permit_location
        if address not in address_list:
            address_list.append(address)
			lookup_address = address + ', Austin, TX'
            found_address = geocoder.google(address)
			geocoder_results.append(found_address)
			row['lat'] = found_address.lat
			row['lng'] = found_address.lng
			row['accuracy'] = found_address.accuracy
		
def write_data(start_date, end_date, data, fh):
    print('Writing data from {} to {}'.format(start_date.format('MM/DD/YYYY'), end_date.format('MM/DD/YYYY')))
    fh.write(data)

def main(start, end):
    fh = open(fname, 'a')
    delta = end - start
    print(delta)
    days = delta.days + 2
    print('Fetching permit reports for {} days'.format(days))
    for day_number in range(0,days,interval):
        start_date = start.replace(days=day_number)
        end_date = start.replace(days=day_number+interval-1)
        try:
            data = get_data(start_date, end_date)
            data = parse_table_html(data)
            write_data(start_date, end_date, data, fh)
        except Exception as e:
            print('Failed to get data for {} to {}'.format(start_date, end_date))
            print(e)
    fh.close()
    
fname = "data/data.txt"
delim = "|"
start = arrow.get(2015,10,15) #  (YYYY,M,D)
end = arrow.get(2015,10,15)
interval = 7 #  7 days is the maximum allowable time interval 
main(start, end)
