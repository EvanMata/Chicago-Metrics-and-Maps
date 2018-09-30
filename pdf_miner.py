from cStringIO import StringIO
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
import os
import sys, getopt
import re

#The pdf this opperates with can be found at:
#https://www.isp.state.il.us/docs/6-260.pdf

#The convert function was borrowed from online at
#http://stanford.edu/~mgorkove/cgi-bin/rpython_tutorials
#/Using%20Python%20to%20Convert%20PDFs%20to%20Text%20Files.php
def convert(fname, pages=None):
    #converts pdf, returns its text content as a string
    if not pages:
        pagenums = set()
    else:
        pagenums = set(pages)

    output = StringIO()
    manager = PDFResourceManager()
    converter = TextConverter(manager, output, laparams=LAParams())
    interpreter = PDFPageInterpreter(manager, converter)

    infile = file(fname, 'rb')
    for page in PDFPage.get_pages(infile, pagenums):
        interpreter.process_page(page)
    infile.close()
    converter.close()
    text = output.getvalue()
    output.close
    return text

def extract_all_info(textfile):
    '''
    Given a text file, find all the IUCR codes with it, and find the 
    categories they correspond to.
    Inputs: textfile - a string.
    Returns: iucrs - a list of strings that are our IUCR codes.
            crime_categories2 - a set of strings.
    '''
    #Cases to ignore - similar formating to IUCRs. 
    non_categories = ["ISP", "UCMJ", "HIV", 'ILCS REFERENCE', \
                      'A', 'B', 'FOID C', 'AWOL']
    iucrs = re.findall(r"[0-9]{4}", textfile)
    crime_categories = re.findall(r"[A-Z][A-Z &]+", textfile)
    crime_categories2 = set()
    for item in crime_categories:
        item = item.strip()
        crime_categories2.add(item)
    
    for item in non_categories:
        if item in crime_categories2:
            crime_categories2.remove(item)
        else:
            print item + " not removed"
    return iucrs, crime_categories2

def compile_info(iucrs, crime_cats):
    '''
    Given a list of iucrs, we know which digits corredpond to what crime 
    categories. Compile all this information into a dictionary.
    Inputs: iucrs - a list of strings of our iucr codes.
            crime_cats - a list of our crime categorie strings.
    Returns: d - a dictionary compiling the information.
    '''
    d = {}
    #This method searches through only once. 
    for crime in crime_cats:
        d[crime] = []
    #Including the - char in re search brings in alot of ignore cases.
    #Instead just add its single use here.
    d['THREAT - TERRORISM'] = []
    #unfortunately, the text that is stripped is in muliple
    #~formats, it seemed faster to recompile this way.
    for iucr in iucrs:
        #Stupid super/extra niche edge cases.
        d0 = int(iucr[0])
        d1 = int(iucr[1])
        d2 = int(iucr[2])
        if iucr == '4310':
            l = d["OTHER OFFENSES"]
        elif iucr == '4510':
            l = d["OTHER OFFENSES"]
            l.append(iucr)
        #Time for many cases.
        else:
            if d0 == 0:
                if d1 == 0:
                    print d0,d1,d2, "X unknown iucr"
                if d1 == 1:
                    l = d["HOMICIDE"]
                    l.append(iucr)
                if d1 == 2:
                    l = d['CRIMINAL SEXUAL ASSAULT']
                    l.append(iucr)
                if d1 == 3:
                    l = d["ROBBERY"]
                    l.append(iucr)
                if d1 == 4:
                    l = d["BATTERY"]
                    l.append(iucr)
                if d1 == 5:
                    l = d["ASSAULT"]
                    l.append(iucr)
                if d1 == 6:
                    l = d["BURGLARY"]
                    l.append(iucr)
                if d1 == 7:
                    l = d['BURGLARY OR THEFT FROM MOTOR VEHICLE']
                    l.append(iucr)
                if d1 == 8:
                    l = d["THEFT"]
                    l.append(iucr)
                if d1 == 9:
                    l = d['MOTOR VEHICLE THEFT']
                    l.append(iucr)
            if d0 == 1:
                if d1 == 0:
                    #edge cases occasionally appear
                    if d2 != 5:
                        l = d["ARSON"]
                        l.append(iucr)
                    else:
                        l = d['HUMAN TRAFFICKING']
                        l.append(iucr)
                if d1 == 1 or d1 == 2:
                    l = d['DECEPTIVE PRACTICES']
                    l.append(iucr)
                if d1 == 3:
                    l = d['CRIMINAL DAMAGE & TRESPASS TO PROPERTY']
                    l.append(iucr)
                if d1 == 4:
                    l = d['DEADLY WEAPONS']
                    l.append(iucr)
                if d1 == 5:
                    l = d['SEX OFFENSES']
                    l.append(iucr)
                if d1 == 6:
                    l = d["GAMBLING"]
                    l.append(iucr)
                if d1 == 7:
                    l = d['OFFENSES INVOLVING CHILDREN']
                    l.append(iucr)
                if d1 == 8:
                    l = d['CANNABIS CONTROL ACT']
                    l.append(iucr)
                if d1 == 9:
                    l = d['METHAMPHETAMINE OFFENSES']
                    l.append(iucr)
            if d0 == 2:
                if d1 == 0:
                    l = d['CONTROLLED SUBSTANCE ACT']
                    l.append(iucr)
                if d1 == 1:
                    if d2 == 1:
                        l = d['HYPODERMIC SYRINGES & NEEDLES ACT']
                        l.append(iucr)
                    else:
                        l = d['DRUG PARAPHERNALIA ACT']
                        l.append(iucr)
                if d1 == 2:
                    l = d['LIQUOR CONTROL ACT VIOLATIONS']
                    l.append(iucr)
                if d1 == 3:
                    l = d['INTOXICATING COMPOUNDS']
                    l.append(iucr)
                if d1 == 4:
                    l = d['MOTOR VEHICLE OFFENSES']
                    l.append(iucr)
                if d1 == 5:
                    l = d["CRIMINAL ABORTION"]
                    l.append(iucr)
                if d1 == 6:
                    print d0,d1,d2, "X unknown iucr"
                if d1 == 7:
                    print d0,d1,d2, "X unknown iucr"
                if d1 == 8 or d1 == 9:
                    l = d["DISORDERLY CONDUCT"]
                    l.append(iucr)
            if d0 == 3:
                if d1 == 0 or d1 == 1 or d1 == 2 or d1 == 3 or \
                          d1 == 4 or d1 ==5:
                    l = d["HOMICIDE"]
                    l.append(iucr)
                if d1 == 6:
                    print d0,d1,d2, "X unknown iucr"
                if d1 == 7 or d1 == 8:
                    l = d["INTERFERENCE WITH PUBLIC OFFICERS"]
                    l.append(iucr)
                if d1 == 9:
                    if d2 == 1 or d2 == 2 or d2 == 3:
                        l = d["INTERFERENCE WITH PUBLIC OFFICERS"]
                        l.append(iucr)
                    else:
                        l = d["INTIMIDATION"]
                        l.append(iucr)
                        
            if d0 == 4:
                if d1 == 0:
                    print d0,d1,d2, "X unknown iucr"
                if d1 == 1:
                    print d0,d1,d2, "X unknown iucr"
                if d1 == 2:
                    l = d["KIDNAPPING"]
                    l.append(iucr)
                if d1 == 3:
                    if d2 == 8:
                        l = d['OTHER OFFENSES']
                        l.append(iucr)
                    else:
                        l = d['THREAT - TERRORISM']
                        l.append(iucr)
                if d1 == 4:
                    l = d['OTHER OFFENSES']
                    l.append(iucr)
                if d1 == 5:
                    l = d['VIOLATION OF CRIMINAL REGISTRY LAWS']
                    l.append(iucr)
            else:
                l = d['OTHER OFFENSES']
                l.append(iucr)
            
    #Could search through the file multiple times - but ineff
    #hom_iucrs == re.findall(r"[0][1][0-9]{2}", textfile)

    #Checking & Refining
    extra_keys = []
    for key in d:
        if d[key] == []:
            extra_keys.append(key)

    for key in extra_keys:
        del d[key]

    return d
        
def compile_info2(iucrs):
    '''
    This function was not used as it turns out the counts don't always 
    correspond nicely to our cateogires. It would output the same way as 
    compile_info.
    '''
    d = {}
    d['HOMICIDE'] = iucrs[0:13]
    d['CRIMINAL SEXUAL ASSULT'] = iucrs[13:18]
    d['ROBBERY'] = iucrs[18:24]
    d['BATTERY'] = iucrs[24:41]
    d['ASSULT'] = iucrs[41:44]
    d['BURGLARY'] = iucrs[44:48]
    d['BURGLARY OR THEFT FROM MOTOR VEHICLE'] = iucrs[48:54]
    d['THEFT'] = iucrs[54:65]
    d['MOTOR VEHICLE THEFT'] = iucrs[66]
    d['ARSON'] = iucrs[67:74]
    d['HUMAN TRAFFICKING'] = iucrs[74:76]
    d['DECEPTIVE PRACTICES'] = iucrs[76:96]
    '''
    d['CRIMINAL DAMAGE & TRESPASS TO PROPERTY'] = iucrs[100:110]
    d['DEADLY WEAPONS'] = iucrs[110:133]
    d['SEX OFFENSES'] = iucrs[]
    d['GAMBLING'] = iucrs[]
    d['OFFENSES INVOLVING CHILDREN'] = iucrs[]
    d['CANNABIS CONTROL ACT'] = iucrs[]
    d['METHAMPHETAMINE OFFENSES'] = iucrs[]
    d['CONTROLLED SUBSTANCE ACT'] = iucrs[]
    d['HYPODERMIC SYRINGES & NEEDLES ACT'] = iucrs[]
    d['DRUG PARAPHERNALIA ACT'] = iucrs[]
    d['LIQUOR CONTROL ACT VIOLATIONS'] = iucrs[]
    d['INTOXICATING COMPOUNDS'] = iucrs[]
    d['MOTOR VEHICLE OFFENSES'] = iucrs[]
    d['CRIMINAL ABORTION'] = iucrs[]
    d['DISORDERLY CONDUCT'] = iucrs[]
    d['INTERFERENCE WITH PUBLIC OFFICERS'] = iucrs[]
    d['INTIMIDATION'] = iucrs[]
    d['KIDNAPPING'] =
    d['THREAT - TERRORISM'] = iucrs[]
    d['VIOLATION OF CRIMINAL REGISTERY LAWS'] = iucrs[]
    d['OTHER OFFENSES'] = iucrs[]
    '''
    return d
    
def iucr_category_to_felonies(d, table_name):
    '''
    Create and print the string we will use to put the IUCR-felony data into a 
    db with columns IUCR_code & felony_class.
    Inputs: d - a dictionary containing all the information we intend to add.
            table_name - a string of the sql db we want to add our info to.
    '''
    Base_str = "INSERT INTO {}".format(table_name)
    Base_str += "\nValues"
    Fel_X = ['HOMICIDE', 'CRIMINAL SEXUAL ASSAULT', 'THREAT - TERRORISM', \
             'METHAMPHETAMINE OFFENSES']
    Fel_1 = ['MOTOR VEHICLE OFFENSES', 'HUMAN TRAFFICKING']
    Fel_2 = ['ROBBERY', 'BURGLARY', 'BURGLARY OR THEFT FROM MOTOR VEHICLE', \
             'MOTOR VEHICLE THEFT', 'ARSON', 'KIDNAPPING', \
             'CRIMINAL ABORTION', 'INTIMIDATION']
    Fel_3 = ['BATTERY', 'SEX OFFENSES', 'DEADLY WEAPONS', \
             'CONTROLLED SUBSTANCE ACT', 'DRUG PARAPHERNALIA ACT', \
             'INTERFERENCE WITH PUBLIC OFFICERS', 'CONTROLLED SUBSTANCE ACT']
    Fel_4 = ['ASSAULT', 'THEFT', 'GAMBLING', 'INTOXICATING COMPOUNDS', \
             'LIQUOR CONTROL ACT VIOLATIONS', 'MOTOR VEHICLE OFFENSES', \
             'VIOLATION OF CRIMINAL REGISTRY LAWS', 'DISORDERLY CONDUCT', \
             'CRIMINAL DAMAGE & TRESPASS TO PROPERTY', 'DECEPTIVE PRACTICES', \
             'HYPODERMIC SYRINGES & NEEDLES ACT', 'CANNABIS CONTROL ACT']
    for key, values in d.items():
        if key in Fel_X:
            for value in values:
                row = '\n({}, {}),'.format(value, 0)
                Base_str += row
        elif key in Fel_1:
            for value in values:
                row = '\n({}, {}),'.format(value, 1)
                Base_str += row
        elif key in Fel_2:
            for value in values:
                row = '\n({}, {}),'.format(value, 2)
                Base_str += row
        elif key in Fel_3:
            for value in values:
                row = '\n({}, {}),'.format(value, 3)
                Base_str += row
        elif key in Fel_4:
            for value in values:
                row = '\n({}, {}),'.format(value, 4)
                Base_str += row
        else:
            #These are two edge cases we do not map, as they 
            if key != 'OTHER OFFENSES' and key != 'OFFENSES INVOLVING CHILDREN':
                key_str = 'key: {}'.format(key)
                val_str = 'icur codes: {}'.format(values)
                print(key_str)
                print(val_str)
                print()
    Base_str = Base_str.strip(',')
    Base_str += ';'
    print(Base_str)





