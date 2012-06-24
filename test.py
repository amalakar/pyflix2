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
        self.config = lambda key: config_parser.get('pyflix', key)
        self.netflix = NetflixAPIV1( appname=self.config('app_name'), 
                                   consumer_key=self.config('consumer_key'),
                                   consumer_secret=self.config('consumer_secret')) 
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
        user = self.netflix.get_user( self.config('access_token'),
                                   self.config('access_token_secret'))
        self.assertIsNotNone(user)
        #dump_object(user)

        details = user.get_details()
        self.assertIsNotNone(details)
        #dump_object(details)

        user_s = user.get_title_states()
        self.assertIsNotNone(user_s)
        #dump_object(user_s)

        feeds = user.get_feeds()
        self.assertIsNotNone(feeds)

        queues = user.get_queues()
        self.assertIsNotNone(queues)

        instant_queues = user.get_queues()
        self.assertIsNotNone(instant_queues)
        dump_object(instant_queues)

        #dump_object(feeds)
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
        self.config = lambda key: config_parser.get('pyflix', key)
        self.netflix = NetflixAPIV2( appname=self.config('app_name'), 
                                   consumer_key=self.config('consumer_key'),
                                   consumer_secret=self.config('consumer_secret'), 
                                   logger=sys.stderr)

    def test_token_functions(self):
        pass
        # I'd love to test the token functions, but unfortunately running these
        # invalidates the existing tokens.  Foo.


    def test_catalog_functions(self):
        # Test the filter capabilities, search with the same search term but with different filter
        # their total result should not match, showing the result set is different
        titles_instant = self.netflix.search_titles('Matrix', max_results=25, filter="instant", expand="@box_art")
        for title in titles_instant[u'catalog']:
            self.assertIsNotNone(title[u'box_art'])
            self.assertIsNotNone(title[u'id'])
        self.assertEqual(int(titles_instant['results_per_page']), 25)

        m = self.netflix.get_title(titles_instant['catalog'][0]['id'])
        self.assertIsNotNone(m)
        #dump_object(m)

        m = self.netflix.get_title(titles_instant['catalog'][0]['id'], "languages_and_audio")
        self.assertIsNotNone(m)
        #dump_object(m)

        titles_disc = self.netflix.search_titles('Matrix', filter="disc")
        self.assertNotEqual(titles_instant['number_of_results'], titles_disc['number_of_results'])

        autocomplete_titles_instant= self.netflix.title_autocomplete("matrix", filter="instant")
        autocomplete_titles_disc = self.netflix.title_autocomplete("matrix", filter="disc")
        
        instant_count = None
        disc_count = None
        if autocomplete_titles_instant['autocomplete']:
            instant_count = len(autocomplete_titles_instant['autocomplete']['title'])
        if autocomplete_titles_disc['autocomplete']:
            disc_count = len(autocomplete_titles_disc['autocomplete']['title'])
        self.assertNotEqual(instant_count, disc_count)

    def test_user_functions(self):
        user = self.netflix.get_user( self.config('access_token'),
                                   self.config('access_token_secret'))
        self.assertIsNotNone(user)
        #dump_object(dir(user))

        details = user.get_details()
        self.assertIsNotNone(details)
        #dump_object(details)

        feeds = user.get_feeds()
        self.assertIsNotNone(feeds)
        #dump_object(feeds)

        title_states = user.get_title_states(["http://api.netflix.com/catalog/titles/movies/20557937", "http://api.netflix.com/catalog/titles/movies/60027695"]) 
        self.assertIsNotNone(title_states)
        #dump_object(title_states)

        queues = user.get_queues(sort_order="alphabetical", start_index=0, max_results=10)
        self.assertIsNotNone(queues)
        dump_object(queues)

        queues_instant = user.get_queues_instant(sort_order="alphabetical", start_index=0, max_results=10)
        self.assertIsNotNone(queues_instant)
        dump_object(queues_instant)
    
        try:
            queues_disc = user.get_queues_disc(sort_order="alphabetical", start_index=0, max_results=10)
            self.assertIsNotNone(queues_disc)
            dump_object(queues_disc)
        except NetflixError as e :
            dump_object(e)


        queues_ia = user.get_queues_instant_available(sort_order="alphabetical", start_index=0, max_results=10)
        self.assertIsNotNone(queues_ia)
        dump_object(queues_ia)

        queues_is = user.get_queues_instant_saved(sort_order="alphabetical", start_index=0, max_results=10)
        self.assertIsNotNone(queues_is)
        dump_object(queues_is)

        rental_history = user.get_rental_history()
        self.assertIsNotNone(rental_history)
        dump_object(rental_history)

        rental_history_watched = user.get_rental_history('watched')
        self.assertIsNotNone(rental_history_watched)
        dump_object(rental_history_watched)

        ratings = user.get_rating(['http://api.netflix.com/catalog/titles/programs/144409/70116820'])
        self.assertIsNotNone(ratings)
        dump_object(ratings)

        ratings_actual = user.get_actual_rating(['http://api.netflix.com/catalog/titles/movies/70090313'])
        self.assertIsNotNone(ratings_actual)
        dump_object(ratings_actual)

        added_rating = user.add_my_rating('http://api.netflix.com/catalog/titles/programs/144409/70116820', 3)
        self.assertIsNotNone(added_rating)
        dump_object(added_rating)

        updated_rating = user.update_my_rating('70116820', 5)
        self.assertIsNotNone(updated_rating)
        dump_object(updated_rating)

        my_rating = user.get_my_rating('70116820')
        self.assertIsNotNone(my_rating)
        dump_object(my_rating)
        
        recommended = user.get_reccomendations()
        self.assertIsNotNone(recommended)
        dump_object(recommended)
        
def dump_object(obj):
    if DUMP_OBJECTS:
        pprint.pprint(obj)

if __name__ == '__main__':
    unittest.main()
