import sqlite3
import csv
import os
import re
import time
import numpy as np
import random as rn
import pandas as pd
import matplotlib.pyplot as plt
from math import radians, cos, sin, asin, sqrt
from sqlite3 import Error

# Source for crime database:
# https://data.cityofchicago.org/Public-Safety/Crimes-2001-to-present/ijzp-q8t2/data

# Use this filename for the database
DATA_DIR = os.path.dirname(__file__)
#DATABASE_NAME = '/home/student/cmsc12200-win-18-eamata/test1.db'
DATABASE_NAME = 'Crime_Weights2.db'
TEST_DATABASE_NAME = '/home/student/cs122-project/Crime_Weights.db'
DATABASE_FILENAME = os.path.join(DATA_DIR, DATABASE_NAME)

def create_db(db_name):
	try:
		connection = sqlite3.connect(db_name)
		print("Success")
	except Error as e:
		print(e)
	finally:
		connection.close()

def collect_iucrs():
	'''
	The IUCR codes in our database are not all in the re format [0-9]{4}.
	Therefore we seek to extract all the iucrs that are not of this
	form so we know what to replace them with. Note all iucrs,
	even improper ones, are 4 characters long.
	'''
	connection = sqlite3.connect(DATABASE_NAME)
	c = connection.cursor()
	command1 = "SELECT DISTINCT IUCR FROM crime"
	original_iucrs = ''
	all_bad_iucrs = []
	w_format_iucrs = c.execute(command1)
	for w_format_iucr in w_format_iucrs:
		w_format_iucr = w_format_iucr[0]
		if not w_format_iucr.isdigit():
			all_bad_iucrs.append(w_format_iucr)
		original_iucrs += w_format_iucr
	other_chars = re.findall(r"[^0-9]+", original_iucrs)
	'''
	Note that by printing other_chars, we know that only single 
	non-digits occur at a time.
	By printing all_bad_chars, we observe that it is always the 4th digit
	which is a letter rather than a number. 
	By observation we can tell the 4th digit is equivalent to a 0.
	'''
	connection.close()
	print(all_bad_iucrs)
	#print(type(original_iucrs[-1]))

def clean_iucrs():
	'''
	Clean our crime table IUCR information, and check that everything worked.
	'''
	connection = sqlite3.connect(DATABASE_NAME)
	c = connection.cursor()
	connection.create_function("Not_Digit", \
            1, not_digit)
	connection.create_function("Correct", \
            1, correct_iucr)
	#command1 = "SELECT REPLACE IUCR FROM crime WHERE Not_Digit(IUCR)"
	command1 = '''
				UPDATE crime SET IUCR = Correct(IUCR) WHERE Not_Digit(IUCR)
				'''
	c.execute(command1)
	connection.commit()
	#Now check if this worked.
	command2 = "SELECT DISTINCT IUCR FROM crime WHERE Not_Digit(IUCR)"
	missed_iucrs = c.execute(command2)
	for iucr in missed_iucrs:
		print(iucr)
	connection.commit()
	connection.close()

def clean_iucrs2():
	'''
	Clean our IUCR table, and check that everything was cleaned.
	'''
	connection = sqlite3.connect(DATABASE_NAME)
	c = connection.cursor()
	connection.create_function("Not_Full", \
            1, Not_full)
	connection.create_function("Correct", \
            1, correct_iucr2)
	#command1 = "SELECT REPLACE IUCR FROM crime WHERE Not_Digit(IUCR)"
	command1 = '''
				UPDATE IUCR SET IUCR_code = Correct(IUCR_code) 
				WHERE Not_Full(IUCR_code)
				'''
	c.execute(command1)
	connection.commit()
	#Now check if this worked.
	command2 = '''
				SELECT DISTINCT IUCR_code, Correct(IUCR_code) FROM IUCR WHERE 
				Not_Full(IUCR_code)
				'''
	missed_iucrs = c.execute(command2)
	for iucr in missed_iucrs:
		print(iucr)
	connection.commit()
	connection.close()

def test_empty_lat_lons():
	connection = sqlite3.connect(DATABASE_NAME)
	c = connection.cursor()
	command1 = '''
				SELECT COUNT(*) FROM crime WHERE Latitude IS NULL
				'''
	IDs = c.execute(command1)
	for ID in IDs:
		print(ID)

	connection.commit()
	connection.close()

def clean_lat_lons():
	#Delete the columns where we do not have the necessary information.
	#Turns out this is only ~1% of our DB.
	connection = sqlite3.connect(DATABASE_NAME)
	c = connection.cursor()
	command1 = '''
				DELETE FROM crime WHERE Latitude IS NULL
				'''
	a = c.execute(command1)
	print("Done deleting I hope.")
	connection.commit()
	connection.close()
	#No longer used, but allowed us to tell what % of our Db we deleted.
	'''
	command3 = 'SELECT COUNT(*) FROM crime'
	count = c.execute(command3)
	for c in count:
		print(c) 
	'''
	
def reduce_years():
	'''
	Our queries are generally significantly slower with the full db. So we 
	only include 2017-2015 (inclusive).
	'''
	connection = sqlite3.connect(DATABASE_NAME)
	c = connection.cursor()
	command1 = '''
				DELETE FROM crime WHERE Year = 
				'''
	yr = 2002
	for i in range(13):
		command2 = command1 + str(yr)
		a = c.execute(command2)
		yr += 1
	connection.commit()
	connection.close()

def compute_weights(mean_time, crime_lon, crime_lat, input_lon, input_lat):
	'''
	Compute the weight of a crime by the formula: if dist < 100: w = mean_time
	else: w = mean_time*100/dist.
	Inputs:
		mean_time - The mean jail crime for the felony associated with our crime
					(a float).
		crime_lon - The longitude of the crime we're evaluating (a float).
		crime_lat - The latitude of the crime we're evaluating (a float).
		input_lon - The Longitude of the location we're evaluating crime_score
					(a float).
		input_lat - The Latitude of the location we're evaluating crime_score
					(a float).			
	'''
	dist = haversine(crime_lon, crime_lat, input_lon, input_lat)
	if dist < 100:
		weight = 1
	else:
		weight = 100./dist
	crime_weight = float(mean_time)*weight
	return crime_weight

def correct_iucr(iucr):
	'''
	By using other functions, we know the only type of IUCR in the original
	csv that is not in our table which maps iucrs to felonies are IUCRS 
	of the form where the last digit is a letter rather than 0.
	'''
	c_iucr = iucr[0:3] + "0"
	return c_iucr

def correct_iucr2(iucr):
	'''
	In addition to the original csv, we add two tables to our db, one of which
	has IUCR codes of the form <space>d2d2d3 rather than 0d1d2d3 
	(where d = digit).
	'''
	iucr = str(iucr)
	c_iucr = '0' + iucr[0:3]
	return c_iucr

def Not_full(iucr):
	if len(str(iucr)) != 4:
		return True
	else:
		return False

def test_correct_iucr():
	'''
	Before we commit our corrected iucrs to the db, we want to check that 
	what we are about to change is correct. So display the IUCR & 
	the corrected IUCRS that are unique.
	'''
	connection = sqlite3.connect(DATABASE_NAME)
	c = connection.cursor()
	connection.create_function("Correct", \
            1, correct_iucr)
	connection.create_function("Not_Digit", 1, not_digit)
	command1 = '''
				SELECT DISTINCT IUCR, Correct(IUCR) FROM crime 
				WHERE Not_Digit(IUCR)
				'''
	c_iucrs = c.execute(command1)
	connection.commit()
	for c_iucr in c_iucrs:
		print(c_iucr)
	connection.close()

def find_crimescore(input_long, input_lat):
	'''
	Given input floats of Longitude and Latitude, find all the crime within
	one kilometer, apply our weighting function to each, and sum them.
	'''
	start = time.time()
	params = (input_long, input_lat, input_long, input_lat)
	#params = (-87.6753, 41.7462, -87.6753, 41.7462)
	#params2 = (-87.6753, 41.7462)
	connection = sqlite3.connect(DATABASE_NAME)
	connection.create_function("Indiv_Score", \
            5, compute_weights)
	connection.create_function("Dist", 4, haversine)
	connection.create_function("Is_Digit", 1, is_digit)
	c = connection.cursor()
	command1 = '''
				SELECT SUM(Indiv_Score(felonies.mean_time, crime.Longitude, 
				crime.Latitude, ?, ?)) AS score FROM crime JOIN IUCR JOIN 
				felonies ON crime.iucr = IUCR.IUCR_code AND IUCR.felony_class = 
				felonies.felony_id WHERE Dist(crime.Longitude, crime.Latitude, 
				?, ?) < 1000
				'''
	crime_score = c.execute(command1, params)
	connection.commit()
	end = time.time()
	print("Time elapsed: " + str(round((end - start), 3)))
	for crime_s in crime_score:
		cs = crime_s[0]
		#Occasionally we have no data in our database for a given area.
		if cs == None:
			return 0
		else:
			cs = float(cs) / 100.0
			if cs > 100:
				return 100
			return float(cs)
	connection.close()


def not_digit(digit):
	return not digit.isdigit()

def is_digit(digit):
	return digit.isdigit()

def csv_to_sql_db(csv_file, table_name, column_names):
	'''
	Given a csv file to add to a sqlite database, take the csv directory
	and the name of the table you wish to create or add to an existing db,
	create the table with all the info from the csv file.
	'''
	#base_str = ".mode csv"
	#base_str2 = ".import {} {}".format(csv_file_dir, table_name)

	column_str = ''
	values_str = ''
	for column in column_names:
		column += ", "
		values_str += "?, "
		column_str += column
	column_str = column_str.strip(", ")
	values_str.strip(", ")

	command1 = "CREATE TABLE {} ({});".format(table_name, column_str)
	connection = sqlite3.connect(DATABASE_NAME)
	print(command1)
	#connection.create_function("compute_distance_between", \
	#4, haversine)
	c = connection.cursor()
	c.execute(command1)
	with open(csv_file) as fin: 
	    #csv.DictReader uses first line in file for column headings by default
	    reader = csv.DictReader(fin)
	    for row in reader:
	    	to_db = []
	    	for j in range(len(column_names)):
	    		row_part = row[str(column_names[j])]
	    		to_db.append(row_part)
	    
	command2 = "INSERT INTO {} ({}) VALUES ({});".format \
		(table_name, column_str, values_str)
	c.executemany(command2, to_db)
	connection.commit()
	connection.close()

def maxs_and_mins():
	'''
	Find the maximum latitude and longitude within our database.
	
	connection = sqlite3.connect(TEST_DATABASE_NAME)
	c = connection.cursor()
	command1 = 
				SELECT MAX(Longitude), MAX(Latitude), MIN(Longitude),
				MIN(Latitude) FROM crimes
				
	c_iucrs = c.execute(command1)
	connection.commit()
	for c_iucr in c_iucrs:
		Ma_long = float(c_iucr[0])
		Ma_lat = float(c_iucr[1])
		Mi_long = float(c_iucr[2])
		Mi_lat = float(c_iucr[3])
	tup = (Ma_long, Ma_lat, Mi_long, Mi_lat)
	
	It turns out that the full databse has a very small (relative)
	number of datapoints very far away from Chicago. So much so that
	if we use them, all other datapoints show up in Chicago. So we set our own
	bounds, from the original testing db (significantly more reasonable).
	'''
	tup2 = (-87.85, 42.05, -87.50, 41.60)
	#print(tup)
	return tup2

def create_indexes():
	'''
	Indexs apparently allow sql databases to not need to re-itterate though
	all the data for the heatmap function. Thus we make lat & long indexes
	to increase performance time.
	'''
	connection = sqlite3.connect(DATABASE_NAME)
	c = connection.cursor()
	command1 = '''
				CREATE INDEX location ON crime (Longitude, Latitude)
				'''
	c.execute(command1)
	connection.commit()
	connection.close()

def score_chi_yr():
	'''
	Opperating on the entire db we calculate the sum of the felony_time's
	for every crime for each year. We then plot these.
	'''
	connection = sqlite3.connect(DATABASE_NAME)
	c = connection.cursor()
	command1 = '''
				SELECT SUM(felonies.mean_time) FROM crime JOIN IUCR 
				JOIN felonies ON crime.IUCR = IUCR.IUCR_code AND 
				IUCR.felony_class = felonies.felony_id WHERE Year = 
				'''
	crime_s_chi = []
	yrs = []
	yr = 2002
	for i in range(16):
		command2 = command1 + str(yr)
		cscores = c.execute(command2)
		for cscore in cscores:
			score = cscore[0]
		crime_s_chi.append(score)
		yrs.append(yr)
		yr += 1
	print(yrs)
	print(crime_s_chi)
	
	plt.plot(yrs, crime_s_chi)
	plt.title("General Crime Trend across Chicago")
	plt.xlabel("Year")
	plt.ylabel("Summed Felony Times")
	plt.show()
	

def rate_of_change_heatmap(year1, year2):
	'''
	Generate the heatmap that represents the change between the heatmaps
	for two different years.
	'''
	file_name1 = "Crime_Heatmap_" + str(year1) + ".csv" 
	file_name2 = "Crime_Heatmap_" + str(year2) + ".csv" 
	heat_info1 = np.genfromtxt(file_name1, delimiter=',')
	heat_info2 = np.genfromtxt(file_name2, delimiter=',')
	heat_info = heat_info2 - heat_info1
	plt.imshow(heat_info, interpolation='nearest')
	plt_title = "Changing Crime Scores Heatmap for Chicago between " \
	+ str(year1) + ' and ' + str(year2)
	plt.title(plt_title)
	plt.colorbar()
	file_name = "Delta_Crime_Heatmap_" + str(year1) + str(year2) + ".csv"
	print(file_name)
	np.savetxt(file_name, heat_info, delimiter=",")
	plt.show()

def heat_map(year):
	'''
	Generate a heat map of crime scores for a given year.
	We first break our db's longitude & latitude ranges into n by n chunks.
	For each chunk, we sum the mean_time of each felony within that chunk.
	This information is added to a matrix, which is then graphed and saved.
	'''
	start = time.time()
	connection = sqlite3.connect(DATABASE_NAME)
	c = connection.cursor()
	command1 = '''
				SELECT SUM(felonies.mean_time) FROM crime JOIN IUCR 
				JOIN felonies ON crime.IUCR = IUCR.IUCR_code AND 
				IUCR.felony_class = felonies.felony_id WHERE Year = ? AND 
				crime.Longitude > ? AND crime.Longitude < ? AND 
				crime.Latitude > ? AND crime.Latitude < ?
				'''
	n = 100
	tup = maxs_and_mins()
	#print(tup)
	Ma_long = tup[0]
	Ma_lat = tup[1]
	Mi_long = tup[2]
	Mi_lat = tup[3]
	grid_pts = np.zeros((n, n))
	#Use this ordering so my heatmap prints in the right orientation.
	grid_lats = np.linspace(Ma_lat, Mi_lat, n + 1)
	grid_lons = np.linspace(Ma_long, Mi_long, n + 1)
	#print(grid_lons, grid_lats)
	for i in range(n):
		for j in range(n):
			local_lat_min = grid_lats[i + 1]
			local_lat_max = grid_lats[i]
			#Use this ordering so my heatmap prints in the right orientation.
			local_long_max = grid_lons[j + 1]
			local_long_min = grid_lons[j]
			params = (year, local_long_min, local_long_max, \
				local_lat_min, local_lat_max)
			#print(params)
			heat_scores = c.execute(command1, params)
			for heat_s in heat_scores:
				heat_score = heat_s[0]
				#print(heat_s)
				if heat_score == None:
					heat_score = 0
				else:
					heat_score = float(heat_score)
			grid_pts[i][j] = heat_score
			#print(i, j)
			#print(grid_pts)
	#print(grid_pts)
	connection.close()
	plt.imshow(grid_pts, cmap='hot', interpolation='nearest')
	plt_title = "Crime Heatmap for Chicago, " + str(year)
	plt.title(plt_title)
	plt.colorbar()
	file_name = "Crime_Heatmap_" + str(year) + ".csv"
	print(file_name)
	np.savetxt(file_name, grid_pts, delimiter=",")
	end = time.time()
	print("Time elapsed: " + str(round((end - start), 3)))
	fig_name = "Heatmap_Chicago_" + str(year) + '.png'
	plt.savefig(fig_name)
	#plt.show()

def normalization_factor():
	'''
	Find the max and min lata & lon in our data, pick a bunch of locations
	within our data range to find the crimescore of, then find the max
	of these and use this as a normalization factor.
	'''
	connection = sqlite3.connect(DATABASE_NAME)
	c = connection.cursor() 
	tup = maxs_and_mins()
	Ma_long = tup[0]
	Ma_lat = tup[1]
	Mi_long = tup[2]
	Mi_lat = tup[3]
	crime_scores = []
	for i in range(100):
		lon = rn.uniform(Mi_long, Ma_long)
		lat = rn.uniform(Mi_lat, Ma_lat)
		#print(lon, lat)
		crime_s = find_crimescore(lon, lat)
		crime_scores.append(crime_s)
	norm_fact = max(crime_scores)
	crime_scores = np.array(crime_scores)/norm_fact
	print("Norm factor is: " + str(norm_fact))
	print()
	print(crime_scores) #Use this data to make a graph of crime scores
	#around the city.

def to_geo_json(d, id1, x_min, x_max, y_min, y_max):
	'''
	d = {"type": "FeatureCollection",
		"features": []
		}
	'''
	features_l = d["features"]
	mini_d = {"type": "Feature", 
			"geometry": {"type": "Polygon",
						"coordinates": [[ [x_min, y_min], [x_min, y_max], 
										[x_max, y_min], [x_max, y_max] ]]}, 
			"properties": {"community": id1}
			}
	features_l.append(mini_d)

def post_processing(Mi_long, Ma_long, Mi_lat, Ma_lat, previous_info):
	heat_info = np.genfromtxt(previous_info, delimiter=',')
	n = len(heat_info)
	d = {"type": "FeatureCollection",
		"features": []
		}
	id_d = {}
	#features_l = d["features"]
	grid_lats = np.linspace(Ma_lat, Mi_lat, n + 1)
	grid_lons = np.linspace(Ma_long, Mi_long, n + 1)
	#print(grid_lons, grid_lats)
	for i in range(n):
		for j in range(n):
			local_lat_min = grid_lats[i + 1]
			local_lat_max = grid_lats[i]
			local_long_min = grid_lons[j]
			local_long_max = grid_lons[j + 1]
			loc_heat = heat_info[i][j]
			id1 = str(i) + '-' + str(j)
			#print(id1)
			id_d[id1] = loc_heat 
			a = to_geo_json(d, id1, local_long_min, local_long_max,\
				local_lat_min, local_lat_max)
	#print(id_d)
	map_dataframe = pd.DataFrame(list(id_d.items()))
	#print(map_dataframe)
	f = open('to_geo_json.txt', 'w')
	f.write(str(d))
	f.close()
	map_dataframe.to_csv('/home/student/cs122-project/map_heats.csv', index = False)
	#db = 'fancy_heat_map.db'
	
	#connection = sqlite3.connect(db)
	#c = connection.cursor()
	#map_dataframe.to_sql('Heat', db, index = False)
	
	#return map_dataframe



def Hyde_park_heatmap():
	'''
	The exact same thing as heatmap, but with specific lat & lon boundaries
	and no year specification.
	'''
	start = time.time()
	connection = sqlite3.connect(DATABASE_NAME)
	c = connection.cursor()
	command1 = '''
				SELECT SUM(felonies.mean_time) FROM crime JOIN IUCR 
				JOIN felonies ON crime.iucr = IUCR.IUCR_code AND 
				IUCR.felony_class = felonies.felony_id WHERE 
				crime.Longitude > ? AND crime.Longitude < ? AND 
				crime.Latitude > ? AND crime.Latitude < ?
				'''
	n = 50
	Mi_long = -87.5742
	Ma_long = -87.60680
	Ma_lat = 41.80270
	Mi_lat = 41.7857
	grid_pts = np.zeros((n, n))
	#Use this ordering so my heatmap prints in the right orientation.
	grid_lats = np.linspace(Ma_lat, Mi_lat, n + 1)
	grid_lons = np.linspace(Ma_long, Mi_long, n + 1)
	#print(grid_lons, grid_lats)
	for i in range(n):
		for j in range(n):
			local_lat_min = grid_lats[i + 1]
			local_lat_max = grid_lats[i]
			#Use this ordering so my heatmap prints in the right orientation.
			local_long_min = grid_lons[j]
			local_long_max = grid_lons[j + 1]
			params = (local_long_min, local_long_max, \
				local_lat_min, local_lat_max)
			#print(params)
			heat_scores = c.execute(command1, params)
			for heat_s in heat_scores:
				heat_score = heat_s[0]
				#print(heat_s)
				if heat_score == None:
					heat_score = 0
				else:
					heat_score = float(heat_score)
					if heat_score > 160:
						lon = (local_long_min + local_long_max)/2.0
						lat = (local_lat_min + local_lat_max)/2.0
						print(lon, lat)
			grid_pts[i][j] = heat_score
			#print(i, j)
			#print(grid_pts)
	#print(grid_pts)
	connection.close()
	plt.imshow(grid_pts, cmap='hot', interpolation='nearest')
	plt_title = "Crime Heatmap for Hyde Park"
	plt.title(plt_title)
	plt.colorbar()
	file_name = "Crime_Heatmap_Hyde_Park2" + ".csv"
	print(file_name)
	np.savetxt(file_name, grid_pts, delimiter=",")
	end = time.time()
	print("Time elapsed: " + str(round((end - start), 3)))
	plt.show()


def haversine(lon1, lat1, lon2, lat2):
	'''
	Calculate the circle distance between two points
	on the earth (specified in decimal degrees)
	'''
	lon1 = float(lon1)
	lat1 = float(lat1)
	lon2 = float(lon2)
	lat2 = float(lat2)
	# convert decimal degrees to radians
	lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

	# haversine formula
	dlon = lon2 - lon1
	dlat = lat2 - lat1
	a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
	c = 2 * asin(sqrt(a))
	# 6367 km is the radius of the Earth
	km = 6367 * c
	m = float(km * 1000)
	return m

a = ["a", "b", "c", "d"]

if __name__ == '__main__':
	#csv_to_sql_db("/home/student/cmsc12200-win-18-eamata/pa4/fodors.csv", "blah7", a)
	#create_db("/home/student/cmsc12200-win-18-eamata/test2.db")
	#clean_iucrs()
	#print("Now finding not clean IUCRs")
	#collect_iucrs()
	#m = haversine(-87.63291666100001, 41.913270306, -87.623435005, 41.837871585)
	#print(m)
	#find_crimescore(-87.6753, 41.7462)
	#print("IUCRs corrected")
	#test_correct_iucr()
	#test_empty_lat_lons()
	#clean_lat_lons()
	#normalization_factor()
	#create_indexes()
	#heat_map(2016)
	#heat_map(2017)
	#Hyde_park_heatmap()
	#score_chi_yr()
	#reduce_years()
	#rate_of_change_heatmap(2016, 2017)
	prev = "Crime_Heatmap_Hyde_Park.csv"
	a = post_processing(-87.5742, -87.60680, 41.7857, 41.80270, prev)

#.mode csv .import /home/student/cmsc12200-win-18-eamata/pa4/fodors.csv fodors
#.mode csv
#.import /home/student/cmsc12200-win-18-eamata/pa4/zagat.csv separate