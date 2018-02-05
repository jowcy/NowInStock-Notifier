import os
import sys
import datetime as dt
import pandas as pd
from pushover import Client ## used to send notifications

## define client for pushover notification service - client and api token come from registering an app with the pushover service
client = Client("<pushover_group_key>",api_token="<app_api_key>")

## log file for storing the last in stock item on NowInStock
log_updatetime = 'gpu_scrape_log.txt'

## check if the log file exists and if it doesnt, use 60 minutes before the current time (datetime.now()).  this was previously hard coded to 1/1/2000 and it generated thousands of notifications.
## stock changes so fast that notifications from 60 minutes ago are probably sold out already.  15 may be more appropriate.
if os.path.isfile(log_updatetime):
        last_runtime = open(log_updatetime,"r").readline()
        last_runtime = dt.datetime.strptime(last_runtime,'%Y-%m-%d %H:%M:%S')
else:
        last_runtime = dt.datetime.strptime(dt.datetime.strptime(str(dt.datetime.now()-dt.timedelta(minutes=60)),'%Y-%m-%d %H:%M:%S.%f').strftime('%Y-%m-%d %H:%M:%S'),'%Y-%m-%d %H:%M:%S')

## the various nowinstock history pages I want to check for new in stock records.  you can't just throw any page in here.  the script queries the very first table in the page
urls = ['https://www.nowinstock.net/computers/videocards/nvidia/gtx1070/full_history.php',
        'https://www.nowinstock.net/computers/videocards/nvidia/gtx1070ti/full_history.php',
        'https://www.nowinstock.net/computers/videocards/nvidia/gtx1080/full_history.php',
        'https://www.nowinstock.net/computers/videocards/nvidia/gtx1080ti/full_history.php',        
        'https://www.nowinstock.net/computers/videocards/amd/rx560/full_history.php',
        'https://www.nowinstock.net/computers/videocards/amd/rx570/full_history.php',
        'https://www.nowinstock.net/computers/videocards/amd/rx580/full_history.php',
        'https://www.nowinstock.net/computers/videocards/amd/rxvega56/full_history.php',
        'https://www.nowinstock.net/computers/videocards/amd/rxvega64/full_history.php']

##  this is used to compare the in stock notification times from nowinstock to each other and determine that last posted in stock notification
##  this value is saved to the log_updatetime file later and is used on each execution as the time to compare in stock notifications to
runtime = None

for url in urls:
        tables = pd.read_html(url)  ## using pandas, read the html from the current url
        table = tables[0]  ## create a single table with the first table in the html
        table.columns = ['Date','Event']  ## name the columns in the table

        for (idx,row)in table.iterrows():  ## iterate through the rows of the table and check if the item is in stock and it was posted since the last in stock notification we read                                
                if "Date/Time" not in row['Date']:  ## the first row in the table contains headers so we are skipping it.  this can probably be eliminated by telling the table to exclude the first row/headers
                        date = dt.datetime.strptime(row['Date'].replace(" EST",""), '%b %d %Y - %I:%M %p')  ## format the date/time string in the html table to date/time

                        if 'In Stock' in row['Event'] and date > last_runtime:  ## check that the table row indicates a product is in stock & that the notification is more recent than our last notification
                                if runtime == None:
                                                runtime = dt.datetime.strptime(row['Date'].replace(" EST",""), '%b %d %Y - %I:%M %p')
                                elif dt.datetime.strptime(row['Date'].replace(" EST",""), '%b %d %Y - %I:%M %p') >= runtime:
                                                runtime = dt.datetime.strptime(row['Date'].replace(" EST",""), '%b %d %Y - %I:%M %p')
                                                
                                event = row['Event']
                                store = event[0:event.find(" - ")]
                                model = event[event.find(" - ")+3:event.find(" In Stock")]
                                searchterm = model.replace(" ","+")

                                if (store=="Newegg"):
                                        store_search = "https://www.newegg.com/Product/ProductList.aspx?Submit=ENE&DEPA=0&Order=BESTMATCH&Description=" + searchterm + "&ignorear=0&N=-1&isNodeId=1"
                                elif (store=="Amazon"):
                                        store_search = "https://smile.amazon.com/s/ref=nb_sb_noss?url=search-alias%3Daps&field-keywords=" + searchterm
                                elif (store=="Best Buy"):
                                        store_search = "https://www.bestbuy.com/site/searchpage.jsp?st=" + searchterm + "&_dyncharset=UTF-8&id=pcat17071&type=page&sc=Global&cp=1&nrp=&sp=&qp=&list=n&af=true&iht=y&usc=All+Categories&ks=960&keys=keys"
                                elif (store=="B&H Photo"):
                                        store_search = "https://www.bhphotovideo.com/c/search?Ntt=" + searchterm + "&N=0&InitialSearch=yes&sts=hist-ma&Top+Nav-Search="
                                else:
                                     store_search = store + " " + model   
                                       
                                print (str(date) + "\t" + event)
                                client.send_message(message="In Stock Page: <a href=\""+url.replace("/full_history.php","")+"\">"+model+"</a><br><br>Store Search Page: <a href=\""+store_search+ "\">"+model+"</a>" ,html=1,title=model + " In Stock @ " + store)
                                # url=url.replace("/full_history.php",""),url_title=model

logfile = open(log_updatetime,"w")
						
if runtime != None:
        logfile.write(str(runtime))
else:
        logfile.write(str(last_runtime))

logfile.close()
