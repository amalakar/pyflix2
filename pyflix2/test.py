# Sample code to use the Netflix python client
import unittest, os
import simplejson
from pprint import pprint
from pyflix2 import *
import ConfigParser
import codecs

DUMP_OBJECTS = True

class TestNetflixAPIV1(unittest.TestCase):

    def setUp(self):
        config_parser = ConfigParser.ConfigParser()
        config_parser.readfp(codecs.open(os.path.expanduser(u'~/.pyflix2.cfg'), u"r", u"utf8"))
        self.config = lambda key: config_parser.get('pyflix2', key)
        self.netflix = NetflixAPIV1( appname=self.config('app_name'), 
                                   consumer_key=self.config('consumer_key'),
                                   consumer_secret=self.config('consumer_secret')) 
                                   #logger=sys.stderr)
        self.user = self.netflix.get_user(self.config('user_id'), self.config('access_token'),
            self.config('access_token_secret'))

    def test_token_functions(self):
        pass


    def test_catalog_functions(self):
        titles = self.netflix.search_titles(u'Matrix', max_results=2)
        for title in titles[u'catalog_titles'][u'catalog_title']:
            self.assertIsNotNone(title[u'title'][u'regular'])
            self.assertIsNotNone(title[u'id'])
        self.assertEqual(len(titles[u'catalog_titles'][u'catalog_title']), 2)

        autocomplete_titles = self.netflix.title_autocomplete(u"matrix")
        for title in autocomplete_titles[u'autocomplete'][u'autocomplete_item']:
            self.assertIn(u'matrix', title['title']['short'].lower())
        people = self.netflix.search_people('Flip Wilson', max_results=5)
        self.assertIsNotNone(people['people'])
        person = self.netflix.get_person(people['people']['person'][0]['id'])
        self.assertIsNotNone(person)

        the_matrix = self.netflix.get_movie_by_title('the matrix')
        self.assertIsNotNone(the_matrix)
        dump_object(the_matrix)


    def test_full_catalog(self):
        # Following call downloads the whole catalog so it is bit of heavy-lifting
        catalog = self.netflix.get_catalog()
        self.assertIsNotNone(catalog)


    def test_user_functions(self):
        self.assertIsNotNone(self.user)
        #dump_object(self.user)

        details = self.user.get_details()
        self.assertIsNotNone(details)
        #dump_object(details)

        user_s = self.user.get_title_states()
        self.assertIsNotNone(user_s)
        #dump_object(user_s)

        feeds = self.user.get_feeds()
        self.assertIsNotNone(feeds)

        queues = self.user.get_queues()
        dump_object(queues)
        self.assertIsNotNone(queues)

        instant_queues = self.user.get_queues()
        self.assertIsNotNone(instant_queues)
        dump_object(instant_queues)

    def test_user_queues(self):
        queues = self.user.get_queues(sort_order="alphabetical", start_index=0, max_results=10)
        self.assertIsNotNone(queues)
        dump_object(queues)

        queues_instant = self.user.get_queues_instant(sort_order="alphabetical", start_index=0, max_results=10)
        self.assertIsNotNone(queues_instant)
        print "Instant Queue Movies:"
        for movie in queues_instant['queue']['queue_item']:
            print movie['title']['short']

        try:
            queues_disc = self.user.get_queues_disc(sort_order="alphabetical", start_index=0, max_results=10)
            self.assertIsNotNone(queues_disc)
            dump_object(queues_disc)
        except NetflixError as e :
            dump_object(e)


        queues_ia = self.user.get_queues_instant_available(sort_order="alphabetical", start_index=0, max_results=10)
        self.assertIsNotNone(queues_ia)
        dump_object(queues_ia)

        queues_is = self.user.get_queues_instant_saved(sort_order="alphabetical", start_index=0, max_results=10)
        self.assertIsNotNone(queues_is)
        dump_object(queues_is)


class TestNetflixAPIV2(unittest.TestCase):

    def setUp(self):
        config_parser = ConfigParser.ConfigParser()
        config_parser.readfp(codecs.open(os.path.expanduser(u'~/.pyflix2.cfg'), u"r", u"utf8"))
        self.config = lambda key: config_parser.get('pyflix2', key)
        self.netflix = NetflixAPIV2( appname=self.config('app_name'), 
                                   consumer_key=self.config('consumer_key'),
                                   consumer_secret=self.config('consumer_secret'), 
                                   logger=sys.stderr)
        self.user = self.netflix.get_user(self.config('user_id'), self.config('access_token'),
                                   self.config('access_token_secret'))

    def test_token_functions(self):
        pass


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

        the_matrix = self.netflix.get_movie_by_title('the matrix')
        self.assertIsNotNone(the_matrix)
        dump_object(the_matrix)

    def test_full_catalog(self):
        # Following call downloads the whole catalog so it is bit of heavy-lifting
        catalog = self.netflix.get_catalog()
        self.assertIsNotNone(catalog)

    def test_user_details(self):
        self.assertIsNotNone(self.user)
        #dump_object(dir(self.user))

        details = self.user.get_details()
        self.assertIsNotNone(details)
        #dump_object(details)

    def test_user_feeds(self):
        feeds = self.user.get_feeds()
        self.assertIsNotNone(feeds)
        for item in feeds['resource']['link']:
            print "%s => %s" % (item['title'], item['href'])
            try:
                #pass
                dump_object(self.user.get_resource(item['href']))
            except NetflixError as e:
                pprint.pprint(e)
        #dump_object(feeds)

    def test_user_states(self):
        title_states = self.user.get_title_states(["http://api.netflix.com/catalog/titles/movies/20557937", "http://api.netflix.com/catalog/titles/movies/60027695"]) 
        self.assertIsNotNone(title_states)
        #dump_object(title_states)

    def test_user_queues(self):
        queues = self.user.get_queues(expand="@title", sort_order="alphabetical", start_index=0, max_results=10)
        self.assertIsNotNone(queues)
        dump_object(queues)

        queues_instant = self.user.get_queues_instant(sort_order="alphabetical", start_index=0, max_results=2)
        self.assertIsNotNone(queues_instant)
        pprint.pprint(queues_instant)
        for queue in queues_instant['queue']:
            q = self.user.get_resource(queue['id'], data={})
            print queue['id']
            print(q.content)

        try:
            queues_disc = self.user.get_queues_disc(sort_order="alphabetical", start_index=0, max_results=10)
            self.assertIsNotNone(queues_disc)
            dump_object(queues_disc)
        except NetflixError as e :
            dump_object(e)


        queues_ia = self.user.get_queues_instant_available(sort_order="alphabetical", start_index=0, max_results=10)
        self.assertIsNotNone(queues_ia)
        dump_object(queues_ia)

        queues_is = self.user.get_queues_instant_saved(sort_order="alphabetical", start_index=0, max_results=10)
        self.assertIsNotNone(queues_is)
        dump_object(queues_is)

    # Not supported by netflix anymore
    def test_user_rental_history(self):
        pass
        rental_history = self.user.get_rental_history(max_results=25)
        self.assertIsNotNone(rental_history)
        dump_object(rental_history)
        self.assertEqual(int(rental_history['results_per_page']), 25)
        movie_ids = []
        for movie in rental_history['rental_history']:
            movie_ids.append(movie['id'])

        ratings = self.user.get_rating(movie_ids)
        dump_object(ratings)

        rental_history_watched = self.user.get_rental_history('watched', start_index=0, max_results=2)
        self.assertIsNotNone(rental_history_watched)
        self.assertEqual(int(rental_history_watched['results_per_page']), 2)
        dump_object(rental_history_watched)

        rental_history_watched = self.user.get_rental_history('shipped')
        self.assertIsNotNone(rental_history_watched)
        dump_object(rental_history_watched)

        try:
            self.user.get_rental_history('bad_type')
            self.assertTrue(False, msg="ValueError exception should have been thrown for incorrect type")
        except ValueError as e:
            dump_object(e)
            self.assertIsNotNone(e)


    def test_user_ratings(self):
        ratings = self.user.get_rating(['http://api.netflix.com/catalog/titles/programs/144409/70116820'])
        self.assertIsNotNone(ratings)
        dump_object(ratings)

        ratings_actual = self.user.get_actual_rating(['http://api.netflix.com/catalog/titles/movies/70090313'])
        self.assertIsNotNone(ratings_actual)
        dump_object(ratings_actual)

        added_rating = self.user.add_my_rating('http://api.netflix.com/catalog/titles/programs/144409/70116820', 3)
        self.assertIsNotNone(added_rating)
        dump_object(added_rating)

        updated_rating = self.user.update_my_rating('70116820', 5)
        self.assertIsNotNone(updated_rating)
        dump_object(updated_rating)

        my_rating = self.user.get_my_rating('70116820')
        self.assertIsNotNone(my_rating)
        dump_object(my_rating)

        predicted_ratings = self.user.get_predicted_ratings(['http://api.netflix.com/catalog/titles/programs/144409/70116820'])
        self.assertIsNotNone(predicted_ratings)
        dump_object(predicted_ratings)

        reco = self.user.get_reccomendations()
        self.assertIsNotNone(reco)
        dump_object(reco)
        for movie in reco['recommendations']:
            self.assertIsNotNone(movie['title']['regular'])


def dump_object(obj):
    if DUMP_OBJECTS:
        pprint.pprint(obj)

if __name__ == '__main__':
    unittest.main()
