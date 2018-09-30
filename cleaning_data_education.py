import pandas as pd
import sqlite3
import numpy as np
from sklearn import preprocessing
from math import radians, cos, sin, asin, sqrt
import seaborn as sns
from statistics import mode
import matplotlib.pyplot as plt


db = sqlite3.connect('ui/education.db')
c = db.cursor()

def haversine(lon1, lat1, lon2, lat2):
    '''
    Calculate the circle distance between two points
    on the earth (specified in decimal degrees)

    This is from pa3
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

def combine():
    '''
    This function calls all other relevant functions to generate a 
    database with all relevant information (SchoolID, Latitude, Longitude, 
    Average Graduation Rate, AverageACT, AverageAP3). Then the function
    normalizes each metric so that it is between 0-100, then computes 
    the final education score and stores it back into the database.
    '''

    create1()
    create2()
    create3()
    create4()

    lst = c.execute('SELECT school_data.SchoolID, Latitude, Longitude,\
     AverageGraduation, AverageACT, AverageAP3 FROM school_data JOIN location \
        ON school_data.SchoolID = location.SchoolID JOIN AverageACT \
        ON location.SchoolID = AverageACT.SchoolID LEFT JOIN AverageAP \
        ON location.SchoolID = AverageAP.SchoolID').fetchall()

    fulldata = pd.DataFrame.from_records(lst, columns = ['SchoolID', 'Latitude',\
     'Longitude','Average Graduation Rate', 'Average ACT', 'AvereageAP3+'])
    fulldata.fillna(0, inplace=True)
    front = fulldata[['SchoolID', 'Latitude', 'Longitude']]    

    #This part takes care of the rescaling
    # Create x, where x the 'scores' column's values as floats
    x = fulldata[['Average Graduation Rate', 'Average ACT',\
     'AvereageAP3+']].values.astype(float)
    # Create a minimum and maximum processor object
    min_max_scaler = preprocessing.MinMaxScaler()
    # Create an object to transform the data to fit minmax processor
    x_scaled = min_max_scaler.fit_transform(x)*100
    # Run the normalizer on the dataframe
    df_scaled = pd.DataFrame(x_scaled)

    df_scaled["score"] = (6/10)*df_scaled[0] + (4/10)*df_scaled[1]\
     + (1/10)*df_scaled[2]

    result = pd.concat([front, df_scaled], axis=1)
    result.rename(columns = {0:'Average Graduation Rate',1:'Average ACT',\
     2:'AvereageAP3+'}, inplace = True)
    result.to_sql('school_metric', db, index = False)

    c.execute('drop table AverageACT')
    c.execute('drop table school_data')
    c.execute('drop table location')
    c.execute('drop table AverageAP')

def create1():
    '''
    Imports the Graduation rate from the csv file and 
    creates a database linking school id to the average draduation rate.
    '''
    
    data = pd.read_csv("Education/Grad rate.csv")
    data.columns = data.iloc[0]
    processed = data[1:][["SchoolID", "2011","2012",\
    "2013","2014","2015","2016","2017"]]
    processed.set_index('SchoolID', inplace=True)
    processed.fillna(np.nan)

    processed['2011'] = processed['2011'].str.replace('%','')
    processed['2012'] = processed['2012'].str.replace('%','')
    processed['2013'] = processed['2013'].str.replace('%','')
    processed['2014'] = processed['2014'].str.replace('%','')
    processed['2015'] = processed['2015'].str.replace('%','')
    processed['2016'] = processed['2016'].str.replace('%','')
    processed['2017'] = processed['2017'].str.replace('%','')

    processed = processed.apply(pd.to_numeric, args=('coerce',))
    processed['AverageGraduation'] = processed.mean(axis=1)
    processed.to_sql('school_data', db, index = True)

def create2():
    '''
    Imports the School locations from the csv file and creates a database linking
    school id to the lat long of each school.
    '''

    data = pd.read_csv("Education/CPS Location.csv")
    processed = data[["SCHOOL_ID","Y","X"]]
    processed.rename(columns = {'SCHOOL_ID': 'SchoolID',\
     'Y':'Latitude','X': 'Longitude'}, inplace = True)
    processed.to_sql('location', db, index = False)

def create3():
    '''
    Imports the ACT data from the csv file and creates a database linking
    school id to the Average composite ACT score of each school.
    '''

    data = pd.read_csv("Education/ACT Score.csv")
    processed = data[["School ID","Composite"]]
    processed.rename(columns = {'School ID':'SchoolID'}, inplace = True)
    processed.to_sql('composite', db, index = False)
    Average_Composite = c.execute('SELECT SchoolID, AVG(Composite) \
        FROM composite GROUP BY SchoolID').fetchall()
    processed = pd.DataFrame.from_records(Average_Composite,\
     columns = ['SchoolID','AverageACT'])
    c.execute('drop table composite')
    processed.fillna(13, inplace=True)
    processed.to_sql('AverageACT', db, index = False)
    #return processed

def create4():
    '''
    Imports the AP data from the csv file and creates a database linking
    school id to the Average percentage of students gettingg 3+ AP scores.
    '''

    data = pd.read_csv("Education/AP Score.csv")
    data.columns = data.iloc[1]
    data.drop(data.index[0], inplace=True)
    data.drop(data.index[0], inplace=True)
    data.columns.values[6] = 'Percentage3'
    data.drop(data[data['Percentage3'] == "*"].index, inplace=True)

    data = data[["SchoolID","Percentage3"]]
    data.to_sql('ap', db, index = False)
    Average_AP = c.execute('SELECT SchoolID, AVG(Percentage3)\
     FROM ap GROUP BY SchoolID').fetchall()
    processed = pd.DataFrame.from_records(Average_AP,\
     columns = ['SchoolID','AverageAP3'])
    processed.to_sql('AverageAP', db, index = False)
    c.execute('drop table ap')
    #return processed

def eduscore(lati,longi,distance):
    '''
    Given a latitude, longitude, and a given radius. Find the education 
    score for that lat long.
    '''

    params = [lati, longi, distance]
    rv = c.execute('SELECT AVG(score) FROM school_metric \
        WHERE haversine(?,?,Latitude,Longitude) < ?', params).fetchall()
    for tup in rv:
        score = list(tup)[0]
        if score > 100:
            score = 100
    return score

def create_heatmap():
    alldata = c.execute('SELECT SchoolID, score FROM school_metric').fetchall()
    data = pd.DataFrame.from_records(alldata, columns=['SchoolID','score'])
    location = pd.read_csv("Education/CPS Location.csv")
    split = pd.DataFrame(location.SCH_ADDR.str.split(',').tolist(),columns = ['PURE','ZIP'])
    idtolocation = pd.concat([location["SCHOOL_ID"], split["PURE"]],axis=1)
    return small



def identify_distribution():
    '''
    We want to identify the best way to normalize the time it takes 
    for a request to be completed by identifying its distribution and working with outliers.
    Input: s (time taken - pandas series)
    '''
    rv = c.execute('SELECT score FROM school_metric').fetchall()
    s = []
    for tup in rv:
        score = list(tup)[0]
        if score > 100:
            score = 100
        s.append(score)

    s = pd.Series(s)

    # take a look at the distribution: 
    sns.distplot(s)
    plt.title('Histogram Eduscore')
    plt.savefig('Histogram Eduscore.png')

    # get key statistics: 
    mu = np.mean(s)
    std = np.std(s)

    print('AVERAGE :', mu)
    print('STDEV :', std)

'''Sources:
Average ACT scores: https://cps.edu/Performance/Documents/Datafiles/AverageACT_2016_SchoolLevel.xls
Graduation rates: https://cps.edu/Performance/Documents/DataFiles/Metrics_CohortGraduationDropout_SchoolLevel_2017.xls
AP Scores : https://cps.edu/Performance/Documents/DataFiles/Metrics_AP_SchoolLevel_2017.xls
Location : https://data.cityofchicago.org/Education/Chicago-Public-Schools-School-Locations-SY1718/4g38-vs8v/data
'''