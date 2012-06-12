from Netflix import *
import getopt
import time 

APP_NAME   = 'netDB'
API_KEY    = '3u2tmnge5649gfx9h9yr9p2j'
API_SECRET = 'VaDCpSfk7B'
CALLBACK   = ''

netflixClient = NetflixClient(APP_NAME, API_KEY, API_SECRET, CALLBACK, 'false')
netflixCatalog = NetflixCatalog(netflixClient)
completeNetflixCatalog = netflixCatalog.getCatalog()
file = open('NetflixCatalog.xml','w')
file.write(completeNetflixCatalog)
file.close()
