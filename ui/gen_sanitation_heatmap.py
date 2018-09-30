'''
File to create a choropleth map for Sanitation. 

We take the sweep areas geo-json file from https://data.cityofchicago.org/Sanitation/Street-Sweeping-2017-Map/qixn-wjxu/data
Then we match each location/request in our database with a sweep area. We sum all the 'scores' of the requests in 
each sweep area. The larger the score, the dirtier the location. We plot the distribution of the scores to 
identify the best way to break our choropleth colors by scores. We did not use straightforward divisions of the colors
since it would result in many areas being labeled equally clean despite having large variations in dirtiness. 
This is because there are extreme outliers (very dirty areas). 
Finally, we use these sweep areas, with the sweep boundaries from the geo-json file to create a choropleth map. 
We chose YlOrRd as our color scheme since it has a broad spectrum of shades that can highlight easily to the viewer
how dirty/clean each area is relative to the others. 
'''

import sqlite3
import pandas as pd
import numpy as np
from math import radians, cos, sin, asin, sqrt, log10
import time
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon, shape
import folium
import json
import seaborn as sns

DB_NAME = 'sanitation.db'
GEOJSON_FILE = 'sweep-area.geojson'
HEATMAP_FILE = 'sanitation-map.html'


# example lat, lon (-87.6753,41.7462)
def check(lat,lon):
    '''
    Find out which sweeping precinct the input lat, lon belong to. 
    '''
    if GEOJSON_FILE:
        with open(GEOJSON_FILE, 'r') as f:
            js = json.load(f)

    # construct point based on lon/lat returned by geocoder
    point = Point(lon,lat)

    # check each polygon to see if it contains the point
    for feature in js['features']:
        polygon = shape(feature['geometry'])
        if polygon.contains(point):
            rv = feature['properties']['code']
            return rv


def map_area(row):
	'''helper function: given a row of request, get the sweeping precinct'''
	return check(row['Latitude'], row['Longitude'])


def create_db_with_area():
    '''
    Create a new table to match all the requests with their sweep area.
    Add the table to the database. This table will be used for calculating
    the scores within each block, and mapped to the heatmap. 
    '''
    db = sqlite3.connect(DB_NAME)
    c = db.cursor()

    df = c.execute('SELECT ID, Score, Latitude, Longitude FROM sanitation')
    df = pd.DataFrame.from_records(df, columns=['index', 'Score', 'Latitude', 'Longitude'])
    df['AreaCode'] = df.apply(map_area, axis=1)
    print('done with area coding')
    df.to_sql('heat', db, index=False)


def area_scores():
    '''
    Calculate the sum of sanitation scores in an area code for all area codes. 
    '''
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    params = None
    select = 'SELECT AreaCode, SUM(Score) AS Scores ' 
    from_ = 'FROM heat ' 
    gb = 'GROUP BY AreaCode'

    query = select + from_ + gb

    return pd.read_sql_query(query, conn)


def check_distribution(area_scores):
    '''
    We want to look at the distribution of scores for the different heatmap sweep areas. 
    '''

    sns.distplot(area_scores.Scores)
    plt.show()
    print(area_scores['Scores'].describe())


def get_color_limit(area_scores):
    # check_distribution(area_scores)

    # we want to identify the dirtiest areas to live (top 5%)
    # and the color the rest of the scores evenly to see cleaniness distribution
    top_95_pct = area_scores['Scores'].quantile(0.95)
    return list(np.linspace(start=0, stop=top_95_pct, num=6))


def create_heatmap():
    ''' 
    Create the choropleth heatmap of sanitation scores based on sweeping area. 
    '''
    gg = area_scores()
    m = folium.Map([41.850000, -87.623177], zoom_start=11)
    thresholds = get_color_limit(gg)
    m.choropleth(
        geo_data=open('sweep-area.geojson').read(),
        data=gg,
        columns=['AreaCode', 'Scores'],
        threshold_scale=thresholds,
        key_on='feature.properties.code',
        fill_color='YlOrRd'
        )

    m.save(HEATMAP_FILE)


