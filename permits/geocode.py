import requests
import time

import geocoder
import secrets


ADDRESS_CACHE = {}
SCRUBBERS = [' EB', ' SB', ' NB', ' WB', 'SVRD', ' AKA ', ' aka ', 'Blk', 'Block of ', '\'', 'UNK ']
SLEEP_TIME = 0.2


def geocode_address(permit_location):
    if permit_location in ADDRESS_CACHE:
        return ADDRESS_CACHE[permit_location]
    if type(permit_location) is not str:
        return

    geocoded_address = geocode_from_coa_address_server(permit_location)
    if not geocoded_address:
        address = permit_location.upper().strip()
        for scrubber in SCRUBBERS:
            address = address.replace(scrubber, ' ')
        address = '{}, Austin, TX'.format(address)

        geocode = geocoder.mapzen(address, key=secrets.MAPZEN_API_KEY)

        geocoded_address = {
            'geocoded_address': geocode.address,
            'geocoder': 'mapzen',
            'lat': geocode.lat,
            'lng': geocode.lng,
            'accuracy': geocode.accuracy,
            'city': geocode.city,
            'county': getattr(geocode, 'county', ''),
            'state': geocode.state,
            'postal_code': geocode.postal,
        }

    ADDRESS_CACHE[permit_location] = geocoded_address
    time.sleep(SLEEP_TIME)

    return geocoded_address


def geocode_from_coa_address_server(permit_location):
    permit_location = permit_location.split('UNIT')[0]
    permit_location = permit_location.split('BLDG')[0]
    permit_location = permit_location.strip()
    url = "http://services.arcgis.com/0L95CJ0VTaxqcmED/ArcGIS/rest/services/LOCATION_address_point/FeatureServer/0/query"
    req = requests.get(url, {
        'where': "full_street_name LIKE '{permit_location}'".format(permit_location=permit_location),
        'outFields': '*',
        'returnGeometry': 'true',
        'outSR': '4326',
        'f': 'pgeojson',
    })
    feature = _get_single_feature_only(req)
    if feature:
        coordinates = feature.get('geometry').get('coordinates')
        city_name = city_name_for_point(*coordinates)
        zipcode = zipcode_for_point(*coordinates)
        props = feature.get('properties')
        return {
            'geocoded_address': props.get('FULL_STREET_NAME'),
            'geocoder': 'coa_addresses',
            'lat': coordinates[1],
            'lng': coordinates[0],
            'city': city_name,
            'postal_code': zipcode,
            'state': 'Texas',
        }


def city_name_for_point(lng, lat):
    """returns city name for a given point, queried from CoA jurisdiction
    boundary data"""
    url = 'http://services.arcgis.com/0L95CJ0VTaxqcmED/ArcGIS/rest/services/BOUNDARIES_jurisdictions/FeatureServer/0/query'
    return _property_where_intersects(url, 'CITY_NAME', lng, lat)


def zipcode_for_point(lng, lat):
    """returns zipcode for a given point, queried from CoA zipcode boundary data"""
    url = 'http://services.arcgis.com/0L95CJ0VTaxqcmED/ArcGIS/rest/services/LOCATION_zipcodes/FeatureServer/0/query'
    return _property_where_intersects(url, 'ZIPCODE', lng, lat)


def _get_single_feature_only(req):
    """returns feature from ArcGIS feature server geojson response only when
    there is a single feature in the response. Returns None if there are no
    features or more than one feature.
    """
    json_response = req.json()
    features = json_response.get('features')
    if features is not None and len(features) != 1:
        return
    else:
        return features[0]


def _property_where_intersects(query_url, property_name, lng, lat):
    """queries for feature that intersects a given point, an returns the value
    of property_name at that point"""
    req = requests.get(query_url, {
        'geometry': '{lng},{lat}'.format(lng=lng, lat=lat),
        'geometryType': 'esriGeometryPoint',
        'inSR': '4326',
        'spatialRel': 'esriSpatialRelIntersects',
        'outFields': '*',
        'returnGeometry': 'false',
        'outSR': '4326',
        'f': 'pgeojson'
    })
    feature = _get_single_feature_only(req)
    if feature:
        return feature['properties'].get(property_name)
    else:
        return ''
