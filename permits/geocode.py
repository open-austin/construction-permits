import operator
import time

import pyproj
import requests

import geocoder
import secrets


ADDRESS_CACHE = {}
SCRUBBERS = [' EB', ' SB', ' NB', ' WB', 'SVRD', ' AKA ', ' aka ', 'Blk', 'Block of ', '\'', 'UNK ']
SLEEP_TIME = 0.2

texas_state_plane = pyproj.Proj("+proj=lcc +lat_1=30.11666666666667 +lat_2=31.88333333333333 +lat_0=29.66666666666667 +lon_0=-100.3333333333333 +x_0=700000 +y_0=3000000 +ellps=GRS80 +datum=NAD83 +to_meter=0.3048006096012192 +units=us-ft +no_defs", preserve_units=True)
wgs84 = pyproj.Proj("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs")


def geocode_address(permit_location):
    if permit_location in ADDRESS_CACHE:
        return ADDRESS_CACHE[permit_location]
    if type(permit_location) is not str:
        return

    geocoded_feature = geocode_from_coa_address_geocoder(permit_location)
    if not geocoded_feature:
        geocoded_feature = geocode_from_coa_feature_server(permit_location)
    if not geocoded_feature:
        geocoded_feature = geocode_from_mapzen(permit_location)

    ADDRESS_CACHE[permit_location] = geocoded_feature
    time.sleep(SLEEP_TIME)

    return geocoded_feature


def geocode_from_coa_address_geocoder(permit_location, score_threshold=95):
    street_name = _split_off_street_name(permit_location)
    json_response = _query_coa_geocoder(street_name)

    if json_response is None:
        return

    try:
        candidates = json_response['candidates']
        best_candidate = sorted(candidates, key=operator.itemgetter('score'))[-1]
    except (IndexError, KeyError, NameError):
        return

    if best_candidate['score'] >= score_threshold:
        location = best_candidate['location']
        x_state_plane = location['x']
        y_state_plane = location['y']
        lng, lat = _state_plane_to_wgs84(x_state_plane, y_state_plane)
        city_name = city_name_for_point(lng, lat)
        zipcode = zipcode_for_point(lng, lat)
        return {
            'geocoded_address': best_candidate.get('address'),
            'geocoder': 'coa_geocoder',
            'lat': lat,
            'lng': lng,
            'city': city_name,
            'postal_code': zipcode,
            'state': 'Texas',
        }


def geocode_from_coa_feature_server(permit_location):
    street_name = _split_off_street_name(permit_location)
    json_response= _query_coa_feature_server(street_name)

    if json_response is None:
        return

    feature = _get_single_feature_only(json_response)
    if feature:
        lng, lat = feature.get('geometry').get('coordinates')
        city_name = city_name_for_point(lng, lat)
        zipcode = zipcode_for_point(lng, lat)
        address = feature.get('properties').get('FULL_STREET_NAME')
        return {
            'geocoded_address': address,
            'geocoder': 'coa_feature_server',
            'lat': lat,
            'lng': lng,
            'city': city_name,
            'postal_code': zipcode,
            'state': 'Texas',
        }


def geocode_from_mapzen(permit_location):
    address = permit_location.upper().strip()
    for scrubber in SCRUBBERS:
        address = address.replace(scrubber, ' ')
    address = '{}, Austin, TX'.format(address)

    geocode = geocoder.mapzen(address, key=secrets.MAPZEN_API_KEY)
    geocoded_feature = {
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
    return geocoded_feature


def city_name_for_point(lng, lat):
    """returns city name for a given point, queried from CoA jurisdiction
    boundary data"""
    url = 'http://services.arcgis.com/0L95CJ0VTaxqcmED/ArcGIS/rest/services/BOUNDARIES_jurisdictions/FeatureServer/0/query'
    return _property_where_intersects(url, 'CITY_NAME', lng, lat)


def zipcode_for_point(lng, lat):
    """returns zipcode for a given point, queried from CoA zipcode boundary data"""
    url = 'http://services.arcgis.com/0L95CJ0VTaxqcmED/ArcGIS/rest/services/LOCATION_zipcodes/FeatureServer/0/query'
    return _property_where_intersects(url, 'ZIPCODE', lng, lat)


def _get_single_feature_only(json_response):
    """returns feature from ArcGIS feature server geojson response only when
    there is a single feature in the response. Returns None if there are no
    features or more than one feature.
    """
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
    json_response = req.json()
    feature = _get_single_feature_only(json_response)
    if feature:
        return feature['properties'].get(property_name)
    else:
        return ''


def _query_coa_geocoder(street_name):
    url = "http://www.austintexas.gov/GIS/REST/Geocode/COA_Composite_Locator/GeocodeServer/findAddressCandidates"
    req = requests.get(url, {
        'street': street_name,
        'f': 'pjson',
    })
    return req.json()


def _query_coa_feature_server(street_name):
    url = "http://services.arcgis.com/0L95CJ0VTaxqcmED/ArcGIS/rest/services/LOCATION_address_point/FeatureServer/0/query"
    req = requests.get(url, {
        'where': "full_street_name LIKE '{street_name}'".format(street_name=street_name),
        'outFields': '*',
        'returnGeometry': 'true',
        'outSR': '4326',
        'f': 'pgeojson',
    })
    return req.json()


def _split_off_street_name(permit_location):
    street_name = permit_location.split('UNIT')[0]
    street_name = street_name.split('BLDG')[0]
    street_name = street_name.strip()
    return street_name


def _state_plane_to_wgs84(x, y):
    return pyproj.transform(texas_state_plane, wgs84, x, y)
