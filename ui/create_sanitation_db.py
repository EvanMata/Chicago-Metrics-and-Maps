'''
File to clean the data and assign a score to each request based on the time taken to complete the request.
'''

import pandas as pd 
import sqlite3
import numpy as np 
import datetime
from math import radians, cos, sin, asin, sqrt, log10
from sklearn import preprocessing
import matplotlib.pyplot as plt
import seaborn as sns
from statistics import mode

DB_NAME = 'sanitation.db'
SANITATION_DATA = 'sanitation_requests.csv'

def identify_distribution(s):
	'''
	We want to identify the best way to normalize the time it takes for a request to be completed 
	by identifying its distribution and working with outliers.
	Input: s (time taken - pandas series)
	'''
	# take a look at the distribution: 
	sns.distplot(s)
	plt.show()
	# data looks very right-skewed with many possible outliers on the right 

	# get key statistics: 
	mu = np.mean(s) # 14.64
	std = np.std(s) # 8.73
	print('mode', mode(s)) # 1
	print('summary', s.describe()) # 25 percentile = 1, median = 4, 75 percentile: 10

	''' 
	Most of the requests are completed within 10 days, which is very reasonable. 

	It looks like the data might be a gamma distribution/chi-square distribution 
	However, we more likely suspect that some entries were keyed in wrongly. For instance,
	it does not seem to make sense that a dirty trash request took over 500 days to complete,
	or for that matter, more than two months.
	'''
	return None


def top_99_pct(s):
	''' 
	For simplicity, we will set the highest 1 percent of the time-taken to be the max of the other 99%
	as a way to treat these outliers. Let us test this
	Input: s (time taken - pandas series) 
	'''
	n = len(s) # 113642
	top_99_pct = s[round(99*n/100)] # 18 
	# This seems like a very reasonable 'maximum' number of days it takes to complete a request. 
	# We return this value, and set all the results with time-taken > top_99_pct to have
	# time taken = top_99_pct

	return top_99_pct 
	

def process_data():
	'''
	Clean up the sanitation database and assign a score to each sanitation request by doing: 
	1. Removing unnecessary columns
	2. Remove irrelevant data
		- sanitation data created before 2011 (sanitation data was first released)
			and after 2018 (sanitation requests may not have been completed)
		- requests made that are unrelated to sanitation
		- data without location data
	3. Assign a score to each sanitation request, and normalize it from 0-100
		We apply log so requests that all requests that take very long will be scored more closely 
	Put the data into sanitation.db
	'''
	db = sqlite3.connect(DB_NAME)
	c = db.cursor()
	c.execute('drop table sanitation') # in recreating the table, we drop the old one. 

	df = pd.read_csv(SANITATION_DATA)

	drop_cols = ['Service Request Number', 'Type of Service Request', \
	'X Coordinate', 'Y Coordinate', 'Location']
	df.drop(drop_cols, axis=1, inplace=True)
	rename_cols = ['CreatedDate', 'Status', 'CompletionDate', 'Issue', 'Address',\
	'ZIP', 'Ward', 'PoliceDistrict', 'CommunityArea', 'Latitude', 'Longitude']
	df.columns = rename_cols

	drop_cols = ['Address', 'ZIP', 'Ward', 'PoliceDistrict', 'CommunityArea']
	# I dropped cols twice since I considered I might want to keep the above location information
	# for heatmapping purposes. I did not. 
	df.drop(drop_cols, axis=1, inplace=True)

	# Fill missing data and ensure that the data is in the correct format.
	df['Issue'] = df.loc[:,'Issue'].fillna('Other')
	df['CreatedDate'] = pd.to_datetime(df.loc[:,'CreatedDate'])
	df['CompletionDate'] = pd.to_datetime(df.loc[:,'CompletionDate'], format="%m/%d/%Y")

	# df['CreatedDate'].isnull().any() ## Check that every entry has a created date

	# for our purposes we will drop duplicate entries
	df = df[df['Status'] != ('Completed - Dup' or 'Open - Dup')]

	# we also remove entries with created date prior to the creation of the dataset
	df = df.loc[(df['CreatedDate'] > '2011-09-30')]
	# we remove requests made this year, 2018: 
	df = df.loc[(df['CreatedDate'] < '2018-01-01')]

	# we remove points that are not related to sanitation and may be more personal in matter
	df = df.loc[(df['Issue'] != 'Graffiti Commercial Vehicle')]

	# we remove points with no lat/lon
	df.dropna(axis=0, how='any', inplace=True)

	df.reset_index(inplace=True) # we want an identifier
	df.rename(columns={'index':'ID'}, inplace=True)
	
	df['Year'] = df['CreatedDate'].map(lambda x: x.year)
	# get date difference to integer
	df['TimeTaken'] = df['CompletionDate'] - df['CreatedDate']
	df['TimeTaken'] = df.loc[:,'TimeTaken'].apply(lambda x: pd.Timedelta(x).days)

	# plot the distribution of the time taken to see if there are any outliers
	# identify_distribution(df.TimeTaken)

	# get the max time-taken as 
	max_tt = top_99_pct(df.TimeTaken)

	df['TimeTaken'] = df.loc[:,'TimeTaken'].apply(lambda x: max_tt if x > max_tt else x)

	# We want to normalize time taken so we can use it for calculations later on
	min_max_scaler = preprocessing.MinMaxScaler()
	np_scaled = min_max_scaler.fit_transform(pd.DataFrame(df['TimeTaken']))
	time_taken_normalized = pd.DataFrame(np_scaled)
	df['Score'] = time_taken_normalized 

	# we rescale using log so that if the scores do not differ significantly when the time taken has been very long 
	# score is between (0,1) for each request
	df['Score'] = df['Score'].apply(lambda x: log10(x+1)/log10(2))
	df = df[['ID','Year', 'CreatedDate', 'CompletionDate', 'Status', 'Latitude', 'Longitude', 'Score']]

	df.to_sql('sanitation', db, index=False)

	return df


if __name__ == '__main__':
	process_data()
