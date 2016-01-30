# City of Austin Construction Permits

A searchable database of construction permits issued by the City of Austin since 1980. 

Data is scraped from http://www.austintexas.gov/oss_permits/permit_report.cfm on a daily basis.

## Usage

Install the requirements:

```
pip install -r requirements.txt
```

Set up a secrets file (`permits/secrets.py`):
```
GITHUB_AUTH=<github auth key>
MAPZEN_API_KEY=<mapzen API key>
```

Get today's construction permits and store them in the `data` directory:

```
python permits/permits.py
```

Run the tests:

```
nosetests
```

Deploy to AWS Lambda:

```
./lambda.sh
```

## Scheduled

Twice a day an AWS lambda job runs `permits.lambda_handler`.

It fetches yesterday's permits, geocodes the addresses, and then uses the GitHub API to commit the data to this repo. This code is Python 2 because is run as an AWS Lambda. Another side effect of being a lambda is we're trying to avoid dependencies with C extensions like pandas.

## License

The code for this repository has been released into the public domain by Open Austin via the Unlicense.

Created by @spatialaustin and @luqmaan.
