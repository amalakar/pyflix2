# Sample code to use the Netflix python client

from pyflix2 import *
import ConfigParser
import argparse
import time 
import sys
import pprint
from time import gmtime, strftime
import codecs

verbose = False
# WARNING : This example script is work in progress, things may be broken


def log(msg, mandatory=False):
    if verbose or mandatory:
        print msg

def get_time(time):
    return strftime("%d %b %Y", gmtime(int(time)))



def get_authorization(netflix, appname):
    """ Get authorization for user and return the User object"""

    (request_token, request_token_secret, url) = netflix.get_request_token(use_OOB = True)
    print "Go to %s sign in and grant permission to netflix account to [%s]" % (url, appname)

    verification_code = unicode(raw_input('Please enter Verifier Code: '), 'utf8')
    (user_id, access_token, access_token_secret) = netflix.get_access_token(request_token, request_token_secret, verification_code)
    print "now put this access_token / access_token_secret in ~/.pyflix2.cfg so you don't have to re-authorize again:\n\n" + \
            "user_id = %s\naccess_token = %s\naccess_token_secret = %s\n\n" % (user_id, access_token, access_token_secret)

    return netflix.get_user(user_id, access_token, access_token_secret)

def autocomplete_search(netflix, term, partial_match=True, filter=None):
    if partial_match:
        # Find the exact movie title by calling autocomplete API then ask user
        log(u"Calling autocomplete API for search string: '%s'" % term)
        if filter:
            log(u"Looking only for movies available on: %s" % filter)
        titles = netflix.title_autocomplete(term, filter=filter)
        movies = []
        if u'title' in titles[u'autocomplete']:
            log(u"Number of results returned %d for search string: '%s'" %
                    (len(titles[u'autocomplete'][u'title']), term), True)
            movies = titles[u'autocomplete'][u'title']
        else:
            print(u"No results found for term: '%s'" % term)
            return

        # Ask user which movie she meant
        for i in range(0, len(movies)):
            print(u"(%d)  %s" % (i, movies[i]))
        choice = int(raw_input(u"\nPlease enter the movie you are interested in: "))
        user_movie_title = movies[choice]
    else:
        # Otherwise we know the exact movie name
        user_movie_title = term

#    search_result = netflix.search_titles(user_movie_title, filter=filter)

    movie = netflix.get_movie_by_title(user_movie_title)

    if movie:
        movie_id = movie['id']
        movie_details = netflix.get_title(movie_id)
        movie_formats = netflix.get_title(movie_id, category=u"format_availability")[u'delivery_formats']
        print u"\nAverage Rating: ", movie_details[u'catalog_title'][u'average_rating']

        genres = []
        for genre in movie_details[u'catalog_title'][u'genres']:
            genres.append(genre[u'name'])

        print u"Genre: %s" % ", ".join(genres)

        print u"ID: ", movie_details[u'catalog_title'][u'id']
        print u"Webpage: ", movie_details[u'catalog_title'][u'web_page']
        print u"Release Year: ", movie_details[u'catalog_title'][u'release_year']

        for format,details in movie_formats.items():
            print format
            if u'available_from' in details:
                print u"\tFrom: ", get_time(details[u'available_from'])
            if u'available_until' in details:
                print u"\tTo: ", get_time(details[u'available_until'])
            for audio, audio_details in details[u'languages_and_audio'].items():
                a = []
                for audio_detail in audio_details[u'audio']:
                    if isinstance(audio_detail[u'label'], basestring):
                        a.append(audio_detail[u'label'])
                    else:
                        a.append(", ".join(audio_detail[u'label']))
                print u"\t%s ( %s )" % (audio, u", ".join(a))
    else:
        print(u"No results found for term: '%s'" % term)
        return


def print_full_catalog(netflix):
    full_catalog = netflix.get_catalog()
    for line in full_catalog.iter_content():
        sys.stdout.write(line)


def main():
    parser = argparse.ArgumentParser(description=u'Command line utility for interacting with Netflix')

    parser.add_argument(u"-v", u"--verbose", action=u"store_true",
                                            help=u"Increse verbosity")

    parser.add_argument(u"-f", u"--full-catalog", action=u"store_true",
                                            help=u"Download the whole catalog of netflix")
    parser.add_argument(u"-a", u"--authorize", action=u"store_true",
                        help=u"Get access token/access token secret for the user")
    parser.add_argument(u"-s", u"--search", type=str, help=u"Search for a movie title")
    parser.add_argument(u"-x", u"--exact-match", action=u"store_false", help=u"Look for exact match")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(u"-d", u"--disc-only", action=u"store_true", help=u"Search only for blu-ray/dvd etc")
    group.add_argument(u"-i", u"--instant-only", action=u"store_true", help=u"Search only for instant titles")
    args = parser.parse_args()

    verbose = args.verbose

    config_parser = ConfigParser.ConfigParser()
    config_parser.readfp(codecs.open(os.path.expanduser(u'~/.pyflix2.cfg'), u"r", u"utf8"))
    config = lambda key: config_parser.get(u'pyflix2', key).strip()
    netflix = NetflixAPIV2( appname=config(u'app_name'),
                                   consumer_key=config(u'consumer_key'),
                                   consumer_secret=config(u'consumer_secret'),
                                   )

    #user = netflix.get_user(config('access_token'), config('access_token_secret'))

    if args.authorize:
        user = get_authorization(netflix, config(u'app_name'))
    elif args.search:
        if args.disc_only:
            filter = u'disc'
        elif args.instant_only:
            filter = u'instant'
        else:
            filter = None

        autocomplete_search(netflix, args.search, partial_match=args.exact_match, filter=filter) 
    elif args.full_catalog:
        print_full_catalog(netflix)
    else:
        parser.print_help()

    return 1

if __name__ == "__main__":
    main()
