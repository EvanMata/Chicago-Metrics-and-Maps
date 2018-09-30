import json
import pandas as pd
from shapely.geometry import Point, Polygon, shape
import sqlite3
import folium
import os

# load GeoJSON file containing sectors

db = sqlite3.connect('ui/education.db')
c = db.cursor()

def check(lat,longi):
    '''
    Check which community area belongs to which community area. This is using
    Shapely to check whether a point belongs in a multipolygon.

    Inputs : Lat, Longitude
    Output : Community area which the Lat, Long belongs to
    '''

    filename = 'commarea.geojson'
    if filename:
        with open(filename, 'r') as f:
            js = json.load(f)

    # construct point based on lon/lat returned by geocoder
    point = Point(longi,lat)

    # check each polygon to see if it contains the point
    for feature in js['features']:
        polygon = shape(feature['geometry'])
        if polygon.contains(point):
            return feature['properties']['community']

def do(row):
    '''
    Function written for pandas apply
    '''

    return check(row['Lat'],row['Long'])

def create():
    '''
    Create a database with names of school and which community 
    area they belong to.
    '''

    sql = c.execute('SELECT score, Latitude, Longitude \
        FROM school_metric').fetchall()
    data = pd.DataFrame.from_records(sql,\
     columns=['score', 'Lat', 'Long'])
    
    data['comm'] = data.apply(do, axis=1)
    data.to_sql('heat', db, index = False)

def main():
    '''
    Creates a dataframe linking community area to score.
    '''

    rv = c.execute('SELECT comm, AVG(score) FROM heat GROUP BY comm').fetchall()
    finalrv = pd.DataFrame.from_records(rv, columns=['comm','score'])
    return finalrv

def createheat():
    '''
    Use folium to create heatmap for education based on GeoJson file 
    with the boudnaries for the community areas. Essentially, 
    folium does the joining of the information automatically. 
    '''

    dat = main()
    m = folium.Map([41.850000, -87.623177], zoom_start=11)
    m.choropleth(
        geo_data=open('commarea.geojson').read(),
        data=dat,
        columns=['comm', 'score'],
        key_on='feature.properties.community',
        fill_color='YlGn',
        )

    m.save('education-map.html')