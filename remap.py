import pandas as pd
import sqlite3

db_name = '/home/student/cs122-project/Crime_Weights2.db'
mydata = pd.read_csv("CPD_crime_data.csv")
db = sqlite3.connect(db_name)
#db = sqlite3.connect('safety.db')
c=db.cursor()

'''
Block commented things did not get used when we needed 
to regenerate the db. Some additional columns added instead.
'''

'''
# create IUCR table
IUCR = pd.read_csv('IUCR.csv')
IUCR.rename(columns = {'PRIMARY DESCRIPTION':'PRIMARY_DESCRIPTION',\
'SECONDARY DESCRIPTION':'SECONDARY_DESCRIPTION'}, inplace = True)
IUCR['IUCR'] = IUCR['IUCR'].str.pad(4, fillchar = '0')
IUCR[['IUCR', 'PRIMARY_DESCRIPTION', 'SECONDARY_DESCRIPTION']].to_sql('iucr_info', db, index = False)
'''

# deselect non-criminal reports:
mydata = mydata.loc[(mydata['Primary Type'] != 'NON-CRIMINAL') & (mydata['Primary Type'] != 'NON-CRIMINAL (SUBJECT SPECIFIED)') & (mydata['Primary Type'] != 'DOMESTIC VIOLENCE')]

# select only the columns that we care about:
mydata = mydata[["Year", "IUCR", "Latitude", "Longitude"]]

'''
mydata = mydata[["ID", "Date", "Year", "IUCR", "Domestic",\
"Location Description", "Block", "Beat"]]
mydata.rename(columns = {"Location Description": "Location_Description"}, inplace = True)
'''

# select non-domestic crimes
mydata = mydata.loc[mydata['Domestic'] == False]

# drop the Domestic column
mydata = mydata[["Year", "IUCR", "Latitude", "Longitude"]]

'''
# drop the Domestic column
mydata = mydata[["ID", "Date", "Year", "IUCR",\
"Location_Description", "Block", "Beat"]]
'''

# select all years but 2018
mydata = mydata.loc[mydata['Year'] != 2018]

# fix mismatch in IUCR codes:
mydata['IUCR'] = mydata['IUCR'].replace({'0840':'1153', '0841':'1154', '0842':'1155', '0843':'1156'})

# put in crime db.
mydata.to_sql('crime', db, index = False)

'''
# create Block_id column and Location_id column
mydata['block_id'] = pd.factorize(mydata['Block'])[0]
mydata['loc_id'] = pd.factorize(mydata['Location_Description'])[0]

mydata[['block_id', 'Block']].to_sql('block_info', db, index = False)
lst = c.execute('select distinct block_id, block from block_info').fetchall()
foo = pd.DataFrame.from_records(lst, columns = ['block_id', 'block_name'])
c.execute('drop table block_info')
foo.to_sql('block_info', db, index = False)

mydata[['loc_id', 'Location_Description']].to_sql('loc_info', db, index = False)
lst = c.execute('select distinct loc_id, location_description from loc_info').fetchall()
foo = pd.DataFrame.from_records(lst, columns = ['loc_id', 'loc_name'])
c.execute('drop table loc_info')
foo.to_sql('loc_info', db, index = False)

# drop Location Description and Block columns now that we have their ids in the SQL database
mydata = mydata[['ID', 'Date', 'Year', 'IUCR', 'loc_id', 'block_id', 'Beat']]
mydata.to_sql('crime', db, index = False)

sample query
c.execute('select date, year, primary_description, secondary_description, loc_name, block_name, beat from crime join block_info join loc_info join iucr_info on crime.block_id = block_info.block_id and crime.loc_id = loc_info.loc_id and crime.iucr=iucr_info.iucr limit 5').fetchall()
'''
