CMSC 12200 - Winter 2018

Group Name: Safety in Chicago

Members: 
- Vu Phan
- Evan Mata 
- Nanut 
- Quinn Nguyen


PROJECT DESCRIPTION

Our primary goal is to create a web interface where users can enter their zip-code (Chicago only) and receive a safety score calculated from the type and frequency of crime in the area from the past 5 years. They will also be able to see the change in safety score over time as a score and as a graph. 

From this data, we will also be generating a geo-heatmap for the whole of Chicago on Matplotlib to visualize the safety score in each area. The heatmap will ideally look something like this: 

Our secondary goal (if time permits), is to combine the crime data set with other data set such as education and healthcare accessibility, to provide additional score such as education score or healthcare score. 


DATA

Our primary source of data is going to be a 1.4 GB file (https://catalog.data.gov/dataset/crimes-2001-to-present-398a4)  on crimes in Chicago from 2001 till the present. It includes information on the time, location, and type of crime and whether an arrest was made, in addition to other factors that we are not interested in. The data comes in various different file types, including csv, which is what we are likely using.  

We will be using other data sources from https://data.cityofchicago.org/ to compute other types of scores.

- Sanitation Score: https://data.cityofchicago.org/Service-Requests/311-Service-Requests-Sanitation-Code-Complaints/me59-5fac 
- Health Score (based on proximity to clinic): https://data.cityofchicago.org/Health-Human-Services/Public-Health-Services-Chicago-Primary-Care-Commun/cjg8-dbka
- Education Score: 

