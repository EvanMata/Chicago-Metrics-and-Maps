import censusgeocode as cg
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import eduscore as edu
import sanitation as sani
import os

DATA_DIR = os.path.dirname(__file__)
numbertoarea = pd.read_csv("GeneralInfo/NumToCom.csv")
data = pd.read_csv("GeneralInfo/CCA201120151.csv")
data.set_index('GEOG', inplace=True)

def link():
    '''
    Creates a dictionary linking the number id of the community area
    to the name of the community
    '''

    numbertoarea.set_index('Number', inplace=True)
    return numbertoarea.to_dict()["Area"]

def link2():
    '''
    Creates a dataframe that links the tract number to the name of the community area.
    '''

    tracttocommunity = pd.read_csv("GeneralInfo/2010TracttoCommunityAreaEquivalencyFile.csv")
    dic = link()
    tracttocommunity.set_index('TRACT', inplace=True)
    tracttocommunity = tracttocommunity[["CHGOCA"]]
    tracttocommunity["Name"] = tracttocommunity.apply(lambda\
     row: dic[row["CHGOCA"]], axis=1)
    return tracttocommunity

tracttocomm = link2()

def address(address):
    '''
    Given an address, use the Geocode API to retrieve tract data and 
    lat/long data which is passed on into the respective compute scores
    function. Furthermore, the function also calls other functions so that
    graphics can be generated
    '''

    result = None
    tract = None
    while result is None:
        try:
            result = cg.address(address, city='Chicago', state='IL')
        except:
            pass

    while tract is None:
        try:
            tract = int(result[0]['geographies']\
                ['2010 Census Blocks'][0]['TRACT'])
        except:
            result = cg.address(address, city='Chicago', state='IL')

    lat = float(result[0]['geographies']['2010 Census Blocks'][0]['INTPTLAT'])
    longi = float(result[0]['geographies']['2010 Census Blocks'][0]['INTPTLON'])
    ed_score = edu.eduscore(lat,longi,1000)
    sa_score = sani.get_sanitation_score(longi, lat)
    racedist(tract, tracttocomm)
    incomedist(tract, tracttocomm)
    agedist(tract, tracttocomm)
    return lat, longi, ed_score, sa_score

def agedist(tract, tracttocomm):
    '''
    Generates a bar graph for the age distribution in a community area,
    given the tract id and a dataframe that links tract id to the commmunity area
    '''

    commnamelist = tracttocomm.loc[tract]
    commname = commnamelist[1]
    stat = data.loc[commname]
    age = stat[1:7].tolist()
    objects = ('Under19', '20-34', '35-49', '50-64', '65-79', 'Over80')
    y_pos = np.arange(len(objects))

    plt.bar(y_pos, age, align='center', alpha=0.5)
    plt.xticks(y_pos, objects)
    plt.ylabel('Number of people')
    plt.title('Age distribution : ' + commname)
    f = os.path.join(DATA_DIR,'static/fig3.png')
    plt.savefig(f)
    plt.close()

def racedist(tract, tracttocomm):
    '''
    Generates a pie chart for the race demographic in a community area,
    given the tract id and a dataframe that links tract id to the commmunity area
    '''

    commnamelist = tracttocomm.loc[tract]
    commname = commnamelist[1]
    stat = data.loc[commname]
    inc = stat[8:13].tolist()

    for i in inc:
        i = i/sum(inc)

    objects = ('White', 'Hispanic', 'Black', 'Asian', 'Other')
    y_pos = np.arange(len(objects))

    plt.pie(inc, labels=objects,
                autopct='%1.1f%%', shadow=False, startangle=90)

    plt.title('Racial Diversity : ' + commname, bbox={'facecolor':'0.8', 'pad':5})
    f = os.path.join(DATA_DIR,'static/fig1.png')
    plt.savefig(f)
    plt.close()

def incomedist(tract, tracttocomm):
    '''
    Generates a bar chart for the income distribution in a community area,
    given the tract id and a dataframe that links tract id to the commmunity area
    '''

    commnamelist = tracttocomm.loc[tract]
    commname = commnamelist[1]
    stat = data.loc[commname]
    age = stat[14:20].tolist()
    objects = ('<25K','25-50K','50-75K','75-100K','100-150K','>150K')
    y_pos = np.arange(len(objects))

    plt.bar(y_pos, age, align='center', alpha=0.5)
    plt.xticks(y_pos, objects)
    plt.ylabel('Number of people')
    plt.title('Income distribution : ' + commname)
    f = os.path.join(DATA_DIR,'static/fig2.png')
    plt.savefig(f)
    plt.close()
    
