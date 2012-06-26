# Sample code to use the Netflix python client

from Netflix import *
import ConfigParser
import getopt
import time 
import sys
import pprint

# WARNING : This exampel script is work in progrees, things may be broken
def get_auth(netflix, appname, verbose):
    (request_token, request_token_secret, url) = netflix.get_request_token(use_OOB = True)
    print "Go to %s sign in and grant permission to netflix account to [%s]" % (url, appname)

    verification_code = raw_input('Please enter Verifier Code:')
    (access_token, access_token_secret) = netflix.get_access_token(request_token, request_token_secret, verification_code)
    print "now put this access_token / access_token_secret in ~/.pyflix.cfg so you don't have to re-authorize again:\n\naccess_token = %s\naccess_token_secret = %s\n\n" % (access_token, access_token_secret)

    return access_token

def do_search(netflix, discs, title):
    ######################################
    # Search for titles matching a string.
    # To view all of the returned object, 
    # you can add a simplejson.dumps(info)
    ######################################  
    print "*** RETRIEVING MOVIES MATCHING %s ***" % title 
    data = netflix.search_titles(title, 0, 10)
    pprint.pprint(data)
    for info in data[u'catalog_title']:
        pprint.pprint(info)
        print info[u'title'][u'short']
        discs.append(info)

def do_autocomplete(netflix,arg):
    ######################################
    # Use autocomplete to retrieve titles
    # starting with a specified string.
    # To view all of the returned object, 
    # you can add a simplejson.dumps(info)
    ######################################  
    print "*** First thing, we'll search for " + arg + " as a string and see if that works ***"
    autocomplete = netflix.catalog.search_string_titles(arg)
    print simplejson.dumps(autocomplete)
    for info in autocomplete:
        print info['title']['short']

def get_title_from_id(netflix,arg):
    ######################################
    # grab a specific title from the ID. 
    # The ID is available as part of the
    # results from most queries (including
    # the ones above.
    ######################################  
    print "*** Now we'll go ahead and try to retrieve a single movie via ID string ***"
    print "Checking for " + arg
    movie = netflix.catalog.get_title(arg)
    if movie['catalog_title']['title']['regular'] == "Flip Wilson":
        print "It's a match, woo!"
    return movie

def get_title_info(netflix,movie):
    ######################################
    # You can retrieve information about 
    # a specific title based on the 'links'
    # which include formats, synopsis, etc.
    ######################################  
    print "*** Let's grab the format for this movie ***"
    disc = NetflixDisc(movie['catalog_title'],netflix)
    formats = disc.get_info('formats')
    print "Formats: %s" % simplejson.dumps(formats,indent=4)

    print "*** And the synopsis ***"
    synopsis = disc.get_info('synopsis')
    print "Synopsis: %s" % simplejson.dumps(synopsis, indent=4)

    print "*** And the cast ***"
    cast = disc.get_info('cast')
    print "Cast: %s" % simplejson.dumps(cast, indent=4)

def find_person(netflix, arg, id):
    ######################################
    # You can search for people or retrieve
    # a specific person once you know their
    # netflix ID
    ######################################  
    print "*** Searching for %s ***" % arg
    person = netflix.catalog.search_people(arg)
    if isinstance(person,dict):
        print simplejson.dumps(person,indent=4)
    elif isinstance(person,list):
        print simplejson.dumps(person[0],indent=4)
    else:
        print "No match"

    print "*** Now let's retrieve a person by ID ***"
    new_person = netflix.catalog.get_person(id)
    if isinstance(new_person,dict):
        print simplejson.dumps(new_person,indent=4)

def get_ratings(netflix,user, discs):
    ######################################
    # Ratings are available from each disc,
    # or if you've got a specific user you
    # can discover their rating, expected
    # rating
    ######################################  
    if (user):
        print "*** Let's grab some ratings for all the titles that matched initially ***"
        ratings =  user.get_ratings( discs )
        print "ratings = %s" % (simplejson.dumps(ratings,indent=4))
    else:
        print "*** No authenticated user, so we'll just look at the average rating for the movies.***"
        for disc in discs:
            print "%s : %s" % (disc['title']['regular'],disc['average_rating'])


def get_user_info(netflix,user):
    print "*** Who is this person? ***"
    user_data = user.get_data()
    print "%s %s" % (user_data['first_name'], user_data['last_name'])

    ######################################
    # User subinfo is accessed similarly
    # to disc subinfo.  Find the field
    # describing the thing you want, then
    # retrieve that url and get that info
    ######################################
    print "*** What are their feeds? ***"
    feeds = user.get_info('feeds')
    print simplejson.dumps(feeds,indent=4)

    print "*** Do they have anything at home? ***"
    feeds = user.get_info('at home')
    print simplejson.dumps(feeds,indent=4)

    print "*** Show me their recommendations ***"
    recommendations = user.get_info('recommendations')
    print simplejson.dumps(recommendations,indent=4)

    ######################################
    # Rental History
    ######################################
    # Simple rental history
    history = netflix.user.get_rental_history()
    print simplejson.dumps(history,indent=4)

    # A little more complicated, let's use mintime to get recent shipments
    history = netflix.user.get_rental_history('shipped',updated_min=1219775019,max_results=4)
    print simplejson.dumps(history,indent=4)

def user_queue(netflix,user):
    ######################################
    # Here's a queue.  Let's play with it
    ######################################
    queue = NetflixUserQueue(netflix.user)
    print "*** Add a movie to the queue ***"
    print simplejson.dumps(queue.get_contents(), indent=4)
    print queue.add_title( urls=["http://api.netflix.com/catalog/titles/movies/60002013"] )
    print "*** Move it to the top! ***"
    print queue.add_title( urls=["http://api.netflix.com/catalog/titles/movies/60002013"], position=1 )
    print "*** Take it out ***"
    print queue.remove_title( id="60002013")

    disc_available = queue.get_available('disc')
    print  "disc_available" + simplejson.dumps(disc_available)
    instant_available =  queue.get_available('instant')
    print "instant_available" + simplejson.dumps(instant_available)
    disc_saved =  queue.get_saved('disc')
    print "disc_saved" + simplejson.dumps(disc_saved)
    instant_saved = queue.get_saved('instant')
    print "instant_saved" + simplejson.dumps(instant_saved)

if __name__ == '__main__':  
    try:
            opts, args = getopt.getopt(sys.argv[1:], "qva")
    except getopt.GetoptError, err:
            # print help information and exit:
            print str(err) # will print something like "option -a not recognized"
            sys.exit(2)

    queuedisc=False
    verbose = False
    usertoken = False
    for o, a in opts:
        if o == "-v":
            verbose = True
        if o == "-q":
            queuedisc = True
        if o == '-a':
            usertoken = True

    config_parser = ConfigParser.ConfigParser()
    config_parser.read(['pyflix.cfg', os.path.expanduser('~/.pyflix.cfg')])
    config = lambda key: config_parser.get('pyflix', key)
    netflix_client = NetflixAPIV1( appname=config('app_name'), 
                                   consumer_key=config('consumer_key'),
                                   consumer_secret=config('consumer_secret'), 
                                   logger=sys.stderr)
    if usertoken:
        access_token = get_auth(netflix_client, config('app_name'), verbose)
        user = NetflixUser(access_token, netflix_client)
    else:
        user = None
    discs=[]

    # Basic search functions
    for arg in args:
        do_search(netflix_client,discs,arg)

    # Note that we have to sleep between queries to avoid the per-second cap on the API
    time.sleep(1)
    do_autocomplete(netflix_client,'Coc')
    time.sleep(1)
    movie = get_title_from_i_d(netflix_client,'http://api.netflix.com/catalog/titles/movies/60002013')
    time.sleep(1)
    get_title_info(netflix_client,movie)
    time.sleep(1)
    find_person(netflix_client,"Harrison Ford", "http://api.netflix.com/catalog/people/78726")

    # Ratings (with/without user)
    if discs:
        get_ratings(netflix_client,user, discs)
        time.sleep(1)

    # User functions
    if user:
        get_user_info(netflix_client,user)
        time.sleep(1)
        user_queue(netflix_client,user)
