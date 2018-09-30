import sqlite3
from math import radians, cos, sin, asin, sqrt

db = sqlite3.connect('education.db', check_same_thread=False)
c = db.cursor()

def haversine(lon1, lat1, lon2, lat2):
    '''
    Calculate the circle distance between two points
    on the earth (specified in decimal degrees)
    '''
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))

    # 6367 km is the radius of the Earth
    km = 6367 * c
    m = 1000*km
    return m

db.create_function("haversine", 4, haversine)

def eduscore(lati,longi,distance):
    '''
    Calculate the education score by accessing the school metric database
    give lat long. A couple of schools have scores higher than 100 so they
    have been normalized, and if there is no schools within 1km radius 
    or out of bounds lat long, the code returns -100. 
    '''
    params = [lati, longi, distance]
    deb = c.execute('SELECT SchoolID, score FROM school_metric WHERE haversine(?,?,Latitude,Longitude) < ?', params).fetchall()
    rv = c.execute('SELECT AVG(score) FROM school_metric WHERE haversine(?,?,Latitude,Longitude) < ?', params).fetchall()
    print(deb)
    for tup in rv:
        score = list(tup)[0]
        if score is not None:
            if score > 100:
                score = 100
            return score
        else:
            return -100