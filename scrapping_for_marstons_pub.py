import os
import selenium
from selenium import webdriver
import time
from PIL import Image
import io
import requests
import pandas as pd
import json
from selenium.common.exceptions import ElementClickInterceptedException
from tqdm import tqdm


driverPath = 'C:/Users/Tony/Downloads/chromedriver_win32/chromedriver.exe'

driver = webdriver.Chrome(driverPath)
#Specify Search URL 
search_url="https://order.marstons.co.uk/"

driver.get(search_url.format(q=''))
#Scroll to the end of the page
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(9)#sleep_between_interactions

#arrary to store the value
pub_name =[]
location =[]
pub_links=[]
links_pub = []


name_results = driver.find_elements_by_tag_name('h3')
loca_results = driver.find_elements_by_tag_name('p')
links = driver.find_elements_by_tag_name("a")

totalResults=len(loca_results)

#extraction of the pub name, location, link
for name in name_results:
    pub_name.append(name.text)
for loca in loca_results:
    location.append(loca.text)
for lnk in links:
    #pub_links.append(lnk.get_attribute('href')+'/order')
    pub_links.append(lnk.get_attribute('href'))



#remove the following index in the link
indexes = [0,501,502,503]
to_del = object()

for index in indexes:
    pub_links[index] = to_del

for _ in indexes:
    pub_links.remove(to_del) 
    
    
#dataframe creation using pandas   
data_pub =pd.DataFrame({'pub_name':pub_name,'location':location, 'pub_links': pub_links})

## scrap the api call for each pub station
api_link=[]
for a in data_pub.pub_links:
    u= a.split("/")[3]
    d='https://api-cdn.orderbee.co.uk/venues/'+ u
    api_link.append('https://api-cdn.orderbee.co.uk/venues/'+ u)
    
#merge api link to datasheet of app the pubs
data_pub.insert(loc=3, column="api_pub_link", value=api_link)

#######################################################################
#######################################################################

#arr to store the content
price_item =[]
name_item=[]
name_pub = []
name_pub_postcode=[]
name_pub_city = []


#code to scrap for each pub api
for i in tqdm(api_link[:500]):
    """from each of the api link in the data_pub"""
    '''keep trying to scrap an api for 5 times to avoid site disconnection'''
    attempts = 5
    while True:
        try:
            r=requests.get(i)
            j = r.json()
            break
        except ConnectionResetError as e:
            if attempt == 0:
                raise ValueError("could not fetch data from api {0}".format(i))
            else:
                attempt = attempt - 1
                print("trying fetching from {0} again. Attempts left: {1}".format(i, attempt))
                continue
        
        
    try:
        """scrap content for menu, menu price,name of pub, address"""
        if "menus" not in j.keys():
            continue # skip this api, not data to scrap
            
        if "oat" not in j["menus"].keys():
            continue # skip this api, not data to scrap
            
        '''scrapping based on the strcuture of the json file for each api'''    
        if 'items' in j['menus']['oat'].keys():
            key_ = 'items'
            for k,v in j['menus']['oat'][key_].items():
                name_item.append(v['name'])
                price_item.append(v['price'])
                name_pub.append(j['slug'])
                name_pub_postcode.append(j['address']['postCode'])
                name_pub_city.append(j['address']['city'])
        elif 'categories' in j['menus']['oat'].keys():
            key_ = 'categories'
            for v in j['menus']['oat'][key_]:
                if len(v['items']) > 0:
                    for g in v['items']:
                        name_item.append(g['name'])
                        price_item.append(g['price'])
                        name_pub.append(j['slug'])
                        name_pub_postcode.append(j['address']['postCode'])
                        name_pub_city.append(j['address']['city'])
                elif len(v['subCategories']) > 0:
                    for b in v['subCategories']:
                        for m in b['items']:
                            name_item.append(m['name'])
                            price_item.append(m['price'])
                            name_pub.append(j['slug'])
                            name_pub_postcode.append(j['address']['postCode'])
                            name_pub_city.append(j['address']['city'])
                else:
                    continue
        else:
            raise ValueError('key error')
    except Exception as e:
        assert False, "here"
    

#dataframe for all data from marstons pub
data=pd.DataFrame({'pub_name':name_pub,'city':name_pub_city,'pub_postcode':name_pub_postcode,'name_item':name_item,'price (£)': price_item})
data.to_csv('data_marstons_pub.csv') #save data in csv file format