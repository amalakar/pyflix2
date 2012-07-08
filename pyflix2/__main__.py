# Sample code to use the Netflix python client

from pyflix2 import *
import ConfigParser
import argparse
import time 
import sys
import pprint
from time import gmtime, strftime
verbose = False
# WARNING : This exampel script is work in progrees, things may be broken


def log(msg, mandatory=False):
    if verbose or mandatory:
        print msg 

def get_time(time):
    return strftime("%d %b %Y", gmtime(int(time)))



def get_authorization(netflix, appname):
    """ Get authorization for user and return the User object"""

    (request_token, request_token_secret, url) = netflix.get_request_token(use_OOB = True)
    print "Go to %s sign in and grant permission to netflix account to [%s]" % (url, appname)

    verification_code = raw_input('Please enter Verifier Code: ')
    (access_token, access_token_secret) = netflix.get_access_token(request_token, request_token_secret, verification_code)
    print "now put this access_token / access_token_secret in ~/.pyflix.cfg so you don't have to re-authorize again:\n\n \
            access_token = %s\naccess_token_secret = %s\n\n" % (access_token, access_token_secret)

    return netflix.get_user(access_token, access_token_secret)

def autocomplete_search(netflix, term, partial_match=True, filter=None):
    if partial_match:
        # Find the exact movie title by calling autocomplete API then ask user
        log("Calling autocomplete API for search string: '%s'" % term)
        if filter:
            log("Looking only for movies available on: %s" % filter)
        titles = netflix.title_autocomplete(term, filter=filter)
        movies = []
        if 'title' in titles['autocomplete']:
            log("Number of results returned %d for search string: '%s'" % 
                    (len(titles['autocomplete']['title']), term), True)
            movies = titles['autocomplete']['title']
        else:
            print("No results found for term: '%s'" % term)
            return

        # Ask user which movie she meant
        for i in range(0, len(movies)):
            print("(%d)  %s" % (i, movies[i]))
        choice = int(raw_input("\nPlease enter the movie you are interested in: "))
        user_movie_title = movies[choice]
    else:
        # Otherwise we know the exact movie name
        user_movie_title = term

    search_result = netflix.search_titles(user_movie_title, filter=filter)

    movie = netflix.get_movie_by_title(user_movie_title)

    if movie:
        movie_id = movie['id']
        movie_details = netflix.get_title(movie_id)
        movie_formats = netflix.get_title(movie_id, category="format_availability")['delivery_formats']
        print "\nAverage Rating: ", movie_details['catalog_title']['average_rating']

        genres = []
        for genre in movie_details['catalog_title']['genres']:
            genres.append(genre['name'])

        print "Genre: %s" % ", ".join(genres)

        print "ID: ", movie_details['catalog_title']['id']
        print "Webpage: ", movie_details['catalog_title']['web_page']
        print "Release Year: ", movie_details['catalog_title']['release_year']

        for format,details in movie_formats.items():
            print format
            print "\tFrom: ", get_time(details['available_from'])
            print "\tTo: ", get_time(details['available_until'])
            for audio, audio_details in details['languages_and_audio'].items():
                a = []
                for audio_detail in audio_details['audio']:
                    a.append(audio_detail['label'])
                print "\t%s ( %s )" % (audio, ", ".join(a))
    else:
        print("No results found for term: '%s'" % term)
        return



def main():
    auth_required = False

    parser = argparse.ArgumentParser(description='Command line utility for interacting with Netflix')
    parser.add_argument("-v", "--verbose", action="store_true",
                                            help="Increse verbosity")
    parser.add_argument("-a", "--authorize", action="store_true", 
                        help="Get access token/access token secret for the user")
    parser.add_argument("-s", "--search", type=str, help="Search for a movie title")
    parser.add_argument("-x", "--exact-match", action="store_false", help="Look for exact match")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-d", "--disc-only", action="store_true", help="Search only for blu-ray/dvd etc")
    group.add_argument("-i", "--instant-only", action="store_true", help="Search only for instant titles")
    args = parser.parse_args()

    verbose = args.verbose

    config_parser = ConfigParser.ConfigParser()
    config_parser.read(['pyflix2.cfg', os.path.expanduser('~/.pyflix2.cfg')])
    config = lambda key: config_parser.get('pyflix2', key).strip()
    netflix = NetflixAPIV2( appname=config('app_name'), 
                                   consumer_key=config('consumer_key'),
                                   consumer_secret=config('consumer_secret'), 
                                   )


    if args.authorize:
        user = get_authorization(netflix, config('app_name'))
    elif auth_required:
        user = netflix.get_user(config('access_token'), config('access_token_secret'))

    if args.search:
        if args.disc_only:
            filter = 'disc'
        elif args.instant_only:
            filter = 'instant'
        else:
            filter = None

        autocomplete_search(netflix, args.search, partial_match=args.exact_match, filter=filter) 

    return 1

if __name__ == "__main__":
    main()
