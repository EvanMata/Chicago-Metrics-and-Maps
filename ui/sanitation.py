'''
File to compute a sanitation score given lat, lon
In this file, we compute the sanitation score by taking the sum of all the sanitation penalties 
in a given 300m radius (the approximate radius we estimate an individual would care about the sanitation level). 

Since we want to get a cleanliness score for the user, we have to take 100 - sanitation_score. 
We realize that our score may go out of range and result in a negative sanitation score. 
Thus, we created helper functions to estimate the maximum possible score a lat/lon in Chicago may achieve, 
and use that knowledge to rescale our cleanliness score accordingly (this scaling is done in Django).
We discover that 3 standard deviations above the mean sanitation score = 147 ~ approximately 150. 
Thus, all scores above 150 receive a cleanliness score of 0, and all scores below 150 
receive a scaled cleanliness score of 100 - 2/3* sanitation_score. 
'''

import sqlite3
from math import radians, cos, sin, asin, sqrt, log10
import time # for timing functions
import seaborn as sns 
import matplotlib.pyplot as plt
import pandas as pd


DB_NAME = 'sanitation.db'


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


def get_sanitation_score(input_lon, input_lat):
	'''
	Given lat, lon as inputs, get all sanitation requests within 300m since residents care 
	about the cleaniness of their immediate surroundings but not much beyond that. 
	'''
	params = (input_lon, input_lat)
	conn = sqlite3.connect(DB_NAME)
	conn.create_function('distance', 4, haversine)
	c = conn.cursor()
	command = 'SELECT SUM(Score) FROM sanitation WHERE distance(Longitude, Latitude, ?, ?) < 300' 
	sanitation_scores = c.execute(command, params)
	conn.commit()
	for score in sanitation_scores: 
		if score[0] == None:
			return 0
		return float(score[0])


def helper_get_multiple_scores(query):
	'''
	Helper function: get a list of sanitation scores based on lat, lon locations obtained from
	a given query
	'''

	conn = sqlite3.connect(DB_NAME)
	conn.create_function('get_score', 2, get_sanitation_score)
	c = conn.cursor()
	command = 'SELECT get_score(?, ?) FROM sanitation'
	lst = []
	all_ll = c.execute(query)
	all_ll = all_ll.fetchall() # list of tuples of lon, lat
	for tup in all_ll:
		score = c.execute(command,tup)
		score = score.fetchone()
		if score[0]:
			lst.append(score[0])

	return lst

def check_max_possible_score():
	'''
	Get the scores of all the crime reports to get the maximum possible score
	'''
	# It takes very long to run across 150k+ rows of data
	# but I can assume, based on the heatmap and reasonable estimation that the 
	# areas least cared for (with longest time to complete a request) have the highest scores

	query = 'SELECT Longitude, Latitude FROM sanitation ORDER BY Score DESC LIMIT 500'
	lst = helper_get_multiple_scores(query)

	return max(lst) # we get 191.48


def plot_1000scores():
	'''
	Plot the distribution of scores of 1000 random locations (with a sanitation request made).
	These scores will be slightly skewed since it does not include locations with no requests made.
	'''
	query = 'SELECT Longitude, Latitude FROM sanitation ORDER BY RANDOM() LIMIT 1000'
	lst = helper_get_multiple_scores(query)
	sns.distplot(lst)
	plt.show()

	s = pd.DataFrame(l)
	s.describe()
	np.std(l) + 3*mean(l) # we get 147.139

	'''We can consider that points more extreme than 3 std from the mean 
	are outliers for simplicity and scale the scores accordingly for the users. 
	'''

	return lst



# example lat, lon (-87.6753,41.7462)

