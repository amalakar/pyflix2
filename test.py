# Sample code to use the Netflix python client
import unittest, os
import simplejson
from pprint import pprint
from Netflix import *
import ConfigParser

MOVIE_TITLE = "Foo Fighters"

DUMP_OBJECTS = True

class TestNetflixAPIV1(unittest.TestCase):

    def setUp(self):
        config_parser = ConfigParser.ConfigParser()
        config_parser.read(['pyflix.cfg', os.path.expanduser('~/.pyflix.cfg')])
        config = lambda key: config_parser.get('pyflix', key)
        self.netflix = NetflixAPIV1( appname=config('app_name'), 
                                   consumer_key=config('consumer_key'),
                                   consumer_secret=config('consumer_secret'), 
                                   access_token=config('access_token'),
                                   access_token_secret=config('access_token_secret'))
                                   #logger=sys.stderr)

    def test_token_functions(self):
        pass
        # I'd love to test the token functions, but unfortunately running these
        # invalidates the existing tokens.  Foo.


    def test_catalog_functions(self):
        titles = self.netflix.search_titles('Matrix', max_results=2)
        for title in titles[u'catalog_titles'][u'catalog_title']:
            self.assertIsNotNone(title[u'title'][u'regular'])
            self.assertIsNotNone(title[u'id'])
            print title['id']
        self.assertEqual(len(titles['catalog_titles'][u'catalog_title']), 2) 

        autocomplete_titles = self.netflix.title_autocomplete("matrix")
        for title in autocomplete_titles[u'autocomplete'][u'autocomplete_item']:
            self.assertIn('matrix', title['title']['short'].lower())

        # Following call downloads the whole catalog so it is bit of heavy-lifting
        # catalog = self.netflix.get_catalog()

        people = self.netflix.search_people('Flip Wilson', max_results=5)
        self.assertIsNotNone(people['people'])
        person = self.netflix.get_person(people['people']['person'][0]['id'])
        self.assertIsNotNone(person)

    def test_user_functions(self):
        user = self.netflix.get_user()
        self.assertIsNotNone(user)
        dump_object(user)
        user_f = self.netflix.get_user_details("feed")
        dump_object(user_f)
        user_s = self.netflix.get_user_details("feed")
        dump_object(user_s)
##    # DISC TESTS
#    def test_disc_functions(self):
#        return  
#        data = netflix_client.catalog.search_titles('Cocoon', 1, 2)
#        test_subject = data[0]
#        disc = NetflixDisc(testSubject, netflix_client)
#        formats = disc.get_info('formats')
#        self.assertIsInstance(formats, dict)
#        synopsis = disc.get_info('synopsis')
#        self.assertIsInstance(synopsis, dict)
#
#    def test_user_functions(self):
#        return 
#        netflix_user = NetflixUser(EXAMPLE_USER,netflixClient)
#        user = netflix_user.get_data()
#        self.assertIsInstance(user['first_name'], str)
#        data = netflix_client.catalog.search_titles('Cocoon',1,2)
#        ratings = netflix_user.getRatings(data)
#        history = netflix_user.get_rental_history('shipped',updated_min=1219775019,max_results=4)
#        pprint(history)
#        self.assertTrue(int(history['rental_history']['number_of_results']) <= 5)
#
#        queue = NetflixUserQueue(netflix_user)
#        response = queue.add_title( urls=["http://api.netflix.com/catalog/titles/movies/60002013"] )
#        response = queue.add_title( urls=["http://api.netflix.com/catalog/titles/movies/60002013"], position=1 )
#        response = queue.remove_title( id="60002013")
#
#        disc_available = queue.get_available('disc')
#        instant_available =  queue.get_available('instant')
#        disc_saved =  queue.get_saved('disc')
#        instant_saved = queue.get_saved('instant')

class TestNetflixAPIV2(unittest.TestCase):

    def setUp(self):
        config_parser = ConfigParser.ConfigParser()
        config_parser.read(['pyflix.cfg', os.path.expanduser('~/.pyflix.cfg')])
        config = lambda key: config_parser.get('pyflix', key)
        self.netflix2 = NetflixAPIV2( appname=config('app_name'), 
                                   consumer_key=config('consumer_key'),
                                   consumer_secret=config('consumer_secret'), 
                                   access_token=config('access_token'),
                                   access_token_secret=config('access_token_secret'),
                                   logger=sys.stderr)

    def test_token_functions(self):
        pass
        # I'd love to test the token functions, but unfortunately running these
        # invalidates the existing tokens.  Foo.


    def test_catalog_functions(self):
        # Test the filter capabilities, search with the same search term but with different filter
        # their total result should not match, showing the result set is different
        titles_instant = self.netflix2.search_titles('Matrix', max_results=25, filter="instant", expand="@box_art")
        for title in titles_instant[u'catalog']:
            self.assertIsNotNone(title[u'box_art'])
            self.assertIsNotNone(title[u'id'])
        self.assertEqual(int(titles_instant['results_per_page']), 25)

        m = self.netflix2.get_title(titles_instant['catalog'][0]['id'])
        self.assertIsNotNone(m)
        #dump_object(m)
        print "--------------"
        m = self.netflix2.get_title(titles_instant['catalog'][0]['id'], "languages_and_audio")
        self.assertIsNotNone(m)
        #dump_object(m)

        titles_disc = self.netflix2.search_titles('Matrix', filter="disc")
        self.assertNotEqual(titles_instant['number_of_results'], titles_disc['number_of_results'])

        autocomplete_titles_instant= self.netflix2.title_autocomplete("matrix", filter="instant")
        autocomplete_titles_disc = self.netflix2.title_autocomplete("matrix", filter="disc")
        
        instant_count = None
        disc_count = None
        if autocomplete_titles_instant['autocomplete']:
            instant_count = len(autocomplete_titles_instant['autocomplete']['title'])
        if autocomplete_titles_disc['autocomplete']:
            disc_count = len(autocomplete_titles_disc['autocomplete']['title'])
        self.assertNotEqual(instant_count, disc_count)

    def test_user_functions(self):
        user = self.netflix2.get_user()
        self.assertIsNotNone(user)
        dump_object(user)

def dump_object(obj):
    if DUMP_OBJECTS:
        pprint.pprint(obj)

if __name__ == '__main__':
    unittest.main()
