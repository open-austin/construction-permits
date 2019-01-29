import math

def convert_to_wgs84(x,y): 
    #  kept these variable declarations from the SQL
    statex = 0
    statey = 0
    metertoft = 3.280839895
    a = 0 # major radius of ellipsoid, map units (NAD 83)
    b = 0 # semiminor axis
    invf = 298.25722210100002
    angrad = 0.017453292519943299 ##number of radians in a degree
    p0 = 0 #  latitude of origin
    p1 = 0 #  latitude of first standard parallel
    p2 = 0 #  latitude of second standard parallel
    m0 = 0  #  central meridian
    x0 = 2296583.333333 #  False easting of central meridian, map units
    y0 = 9842500.000000 #  False northing
    pi = 3.14159265358979
    ec = 0 #  eccentricity of ellipsoid (NAD 83)
    rho = 0
    rho0 = 0
    theta = 0
    txy = 0
    lon0 = 0
    lat0 = 0
    m1 = 0
    m2 = 0
    t0 = 0
    t1 = 0
    t2 = 0
    n = 0
    f = 0
    ux = 0
    uy = 0
    part1 = 0
    lat1 = 0
    latitude = 0
    longitude = 0

    #  BEGIN
    statex = x
    statey = y
    ec = math.sqrt((1 / invf) * (2 - (1 / invf)))

    a = 6378137.0 * metertoft #  major radius of ellipsoid, map units (NAD 83)
    b = 6356752.3141403561 * metertoft
    p0 = 29.666667 * angrad #  latitude of origin
    p1 = 30.116667 * angrad #  latitude of first standard parallel
    p2 = 31.883333 * angrad #  latitude of second standard parallel
    m0 = -100.333333 * angrad #  central meridian

    #  Calculate the coordinate system constants.
    m1 = math.cos(p1) / math.sqrt(1 - (math.pow(ec, 2)) * math.pow(math.sin(p1), 2))
    m2 = math.cos(p2) / math.sqrt(1 - (math.pow(ec, 2)) * math.pow(math.sin(p2), 2))
    t0 = math.tan(pi / 4 - (p0 / 2))
    t1 = math.tan(pi / 4 - (p1 / 2))
    t2 = math.tan(pi / 4 - (p2 / 2))

    t0 = t0 / math.pow(((1 - (ec * (math.sin(p0)))) / (1 + (ec * (math.sin(p0))))), ec / 2)
    t1 = t1 / math.pow(((1 - (ec * (math.sin(p1)))) / (1 + (ec * (math.sin(p1))))), ec / 2)
    t2 = t2 / math.pow(((1 - (ec * (math.sin(p2)))) / (1 + (ec * (math.sin(p2))))), ec / 2)

    n = math.log10(m1 / m2) / math.log10(t1 / t2)
    f = m1 / (n * math.pow(t1, n))
    rho0 = a * f * math.pow(t0, n)

    #  Convert the coordinate to Latitude/Longitude.
    #  Calculate the Longitude.
    ux = statex - x0
    uy = statey - y0

    rho = math.sqrt(math.pow(ux, 2) + math.pow((rho0 - uy), 2))

    theta = math.atan(ux / (rho0 - uy))
    txy = math.pow((rho / (a * f)), (1 / n))
    lon0 = (theta / n) + m0
    ux = ux + x0

    #  Estimate the Latitude
    lat0 = pi / 2 - (2 * math.atan(txy))

    #  Substitute the estimate into the iterative calculation that
    #  converges on the correct Latitude value.

    part1 = (1 - (ec * math.sin(lat0))) / (1 + (ec * math.sin(lat0)))

    lat1 = pi / 2 - (2 * math.atan(txy * math.pow(part1, (ec / 2))))

    while ((abs(lat1 - lat0)) > 0.000000002):
        lat0 = lat1
        part1 = (1 - (ec * math.sin(lat0))) / (1 + (ec * math.sin(lat0)))
        lat1 = pi / 2 - (2 * math.atan(txy * math.pow(part1, (ec / 2))))

    #  Convert from radians to degrees.
    latitude = lat1 / angrad
    longitude = lon0 / angrad
    
    print(latitude, longitude)
    
    return latitude,longitude
