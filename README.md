# City of Austin Construction Permits

Data scraped from http://www.austintexas.gov/oss_permits/permit_report.cfm.

## Usage

Install the requirements:

```
pip install -r requirements.txt
```

Get today's construction permits and store them in the `data` directory:

```
python src/permits.py
```

Run the tests:

```
nosetests
```

## Scheduled

Once a day an AWS lambda job runs `python src/main.py` on yesterday's permits. It then commits the data to this repo. Because this is run as AWS Lambda this code is in Python 2. Also, we're trying to avoid libraries with CSV extensions (like pandas or lxml).

## License

The code for this repository has been released into the public domain by Open Austin via the Unlicense.
