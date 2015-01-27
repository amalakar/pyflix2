""" Library for accessing the REST API from Netflix
"""

import sys
import os.path
import requests
from requests_oauthlib import OAuth1
import pprint
import time
from datetime import datetime
from urlparse import urlparse, parse_qs, parse_qsl, urlunparse
import urllib
import json

__version__ = u"0.2.1"

BASE_URL= u'http://api-public.netflix.com'
AUTH_BASE_URL = BASE_URL 

REQUEST_TOKEN_URL = AUTH_BASE_URL + u'/oauth/request_token'
ACCESS_TOKEN_URL = AUTH_BASE_URL + u'/oauth/access_token'
AUTHORIZATION_URL = u'https://api-user.netflix.com/oauth/authenticate'
AUTHORIZATION_URL = u'https://api-user.netflix.com/oauth/authenticate'
NETFLIX_FILTER = {'disc': BASE_URL + '/categories/title_formats/disc',
                  'instant': BASE_URL + '/categories/title_formats/instant'}
EXPANDS = [u"@title", u"@box_art", u"@synopsis", u"@short_synopsis", u"@format_availability", u"@screen_formats",
          u"@cast", u"@directors", u"@languages_and_audio", u"@awards", u"@similars", u"@bonus_materials",
          u"@seasons", u"@episodes", u"@discs"]
""" Allowed expand strings while calling the titles api"""

SORT_ORDER = ["queue_sequence", "date_added", "alphabetical"]
""" Allowed sort order while retrieveing queues"""

RENTAL_HISTORY_TYPE = ['shipped', 'returned', 'watched']
""" Allowed type to use while calling :py:meth:`~User.get_rental_history`"""

GENERIC_CATALOG_TYPES = ['streaming', 'dvd']

CATALOG_TYPES_V1 = ['index'] + GENERIC_CATALOG_TYPES
""" Allowed catalog type to use while calling :py:meth:`~NetflixAPIV1.get_catalog`"""

CATALOG_TYPES_V2 = ['full'] + GENERIC_CATALOG_TYPES
""" Allowed catalog type to use while calling :py:meth:`~NetflixAPIV2.get_catalog`"""

class NetflixError(Exception):
    """ Error thrown if the netflix api throws http error"""
    pass


class NetflixAuthRequiredError(Exception):
    """ Error thrown if authorization is required"""
    pass


class _NetflixAPI(object):
    """ Abstract Class for the common api of Netflix V1.0 and V2.0"""

    _api_version = 2.0

    def __init__(self, appname, consumer_key, consumer_secret, logger=None):
        """ **Abstract class** contains all the common functionality of netflix v1 and v2 REST api

        :param appname: The Application name as registered in Netflix Developer 
            website <http://developer.netflix.com/apps/mykeys>
        :param consumer_key: The consumer key as registered in Netlflix Developer website
        :param consumer_secret: The consumer secret as registerde in Netflix Developer website
        :param logger: (Optional) The stream object to write log to. Nothing is logged if `logger` is `None`
        """

        # Abstractify this class
        if self.__class__ is _NetflixAPI:
            raise NotImplementedError
        if not appname:
            raise NetflixError("appname cannot be null/empty")
        if not consumer_key:
            raise NetflixError("consumer_key cannot be null/empty")
        if not consumer_secret:
            raise NetflixError("consumer_secret cannot be null/empty")
        self._consumer_name = appname.strip()
        self._consumer_key = consumer_key.strip()
        self._consumer_secret = consumer_secret.strip()

        oauth = OAuth1(self._consumer_key, client_secret=self._consumer_secret)
        self._logger = logger

        self._client = requests.Session()
        self._client.auth = oauth

    def get_request_token(self, use_OOB = True):
        """Obtains the request token/secret and the authentication URL

        url: /oauth/request_token

        :param use_OOB: (Optional) If set to false the oauth out-of-bound authentication is used
            which requires the user to go to nerflix website and get the verfication code
            and provide here

        :Returns:
            Returns the triplet ``(request_token, request_token_secret , url)``
        :rtype: (string, string, string)
        """

        # Step 1: Obtain the request Token
        oauth = OAuth1(self._consumer_key, client_secret=self._consumer_secret)
        if use_OOB:
            data = {u'oauth_callback': u'oob'}
        else:
            data = {}
        response = requests.post(REQUEST_TOKEN_URL, auth=oauth, data=data, allow_redirects=True)
        response = parse_qs(response.text)
        request_token = response['oauth_token'][0]
        request_secret = response['oauth_token_secret'][0]

        # Step 2: User needs to visit the netflix authentication URL in browser
        # A) User obtains the out-of-bound verification code by visiting the netflix authentication URL (if oob is enabled)
        # B) User grants permission to the app by visiting the netflix authentication URL (if oob is disabled)

        # Build the netflix authentication url, the login_url in response itself is not sufficient. 
        # The url needs the application_name as well as the consumer key, so append them
        params = {'application_name': self._consumer_name,
                    'oauth_consumer_key': self._consumer_key}
        auth_url = self._append_param(response['login_url'][0], params)
        return request_token, request_secret, auth_url

    def get_access_token(self, request_token, request_token_secret, oauth_verification_code = None):
        """Obtains the access token/secret, given:

            - The ``request_token`` and ``request_token_secret`` has been authorized  by visiting the netflix authorization URL by user
            - The user has obtained the verification code (when ``use_OOB`` was set in ``get_request_token`` from netflix website)

        url: /oauth/access_token

        :param request_token: The request token obtained using :meth: get_request_token 
        :param request_token_secret: The request token secret obtained using :py:meth:`~NetflixAPI.get_request_token`
        :param oauth_verification_code: (Optional) The verification code obtained from netflix website, if ``use_OOB`` 
            was set to ``True`` in :py:meth:`~NetflixAPIV2.get_request_token`

        :Returns:
            Returns the triplet ``(user_id, access_token, access_token_secret)``
        :rtype: (string, string, string)
        """

        # Step 3: Obtain access token
        if oauth_verification_code:
            oauth = OAuth1(self._consumer_key, client_secret=self._consumer_secret,  resource_owner_key=request_token,
                resource_owner_secret=request_token_secret, verifier=oauth_verification_code)
        else:
            oauth = OAuth1(self._consumer_key, client_secret=self._consumer_secret,  resource_owner_key=request_token,
                resource_owner_secret=request_token_secret)
        response = requests.post(ACCESS_TOKEN_URL, auth=oauth)

        response = parse_qs(response.text)
        return response[u'user_id'][0], response[u'oauth_token'][0], response[u'oauth_token_secret'][0]

    def search_titles(self, term, filter=None, expand=None, start_index=None, max_results=None):
        """Use the catalog titles resource to search the netflix movie catalog(includes all medium)
        for titles of movies and television series. 

        url: /catalog/titles

        :param term: The word or term to search the catalog for. The Netflix
            API searches the title and synopses of catalog titles for a match.
        :param filter: (optional) The filter could be either the string `"instant"` or `"disc"`
        :param expand: (optional) The expand parameter instructs the API to expand the ``expand``
            (``@title, @box_art``, see :py:data:`EXPANDS`)  part of data and include that data inline in the element
        :param start_index:  (optional) The zero-based offset into the list that results
            from the query. By using this with the max_results parameter, user
        :param max_results: (optinoal) The maximum number of results to return. 
            This number cannot be greater than 100. If you do not specify 
            `max_results`, the default value is 25. can request successive pages of search results.

        :Returns:
            Returns the matching titles as a series of `catalog_title` records in relevance order, 
            and the total number of results in `results_per_page`.
        """

        url_path = '/catalog/titles'
        data = {'term': term, 'output': 'json',
                     'start_index': start_index, 'max_results': max_results}
        if filter:
            data['filters'] = NETFLIX_FILTER[filter]
        if expand and EXPANDS.index(expand) >= 0:
            data['expand'] = expand
        return self._request("get", url_path, data).json()

  
    def title_autocomplete(self, term, filter=None, start_index=None, max_results=None):
        """ Searches the catalog for  for movies and television series whose "short" 
        titles match a partial search text. You can then pass the title names that 
        Netflix API returns from this request to the title search methods in order 
        to conduct the actual title search. You can only autocomplete titles 
        (not other items, like names of actors).

        url: /catalog/titles/autocomplete

        :param term: The string to look for partial match in short titles
        :param start_index:  (optional) The zero-based offset into the list that results from the query.
        :param filter: (Optional) The filter could be either the string `"instant"` or `"disc"`
        :param max_results: (optinoal) The maximum number of results to return. 

        :Returns:
             Returns a list of movie and television title names that match your partial search text. 
        """

        url_path = '/catalog/titles/autocomplete'
        data = {'term': term,
                     'start_index': start_index, 'max_results': max_results}

        if filter:
            data['filters'] = NETFLIX_FILTER[filter]
        return self._request("get", url_path, data).json()




    def get_title(self, id,  category=None):
        """ Retrieve details for specific catalog title

        url: /catalog/titles/movies/title_id, /catalog/titles/series/series_id, /catalog/titles/series/series_id/seasons/season_id, /catalog/titles/programs/program_id

        :param id: This is the id that is returned for movies in ``search_movie`` call (id looks like
            ``http://api.netflix.com/catalog/titles/movies/60000870``)
        :param category: The expand parameter instructs the API to get (``"title", "box_art"``, 
            see :py:data:`EXPANDS` without the `@` though)  information of the movie

        :returns: 
            The detail of the movie **OR** (award/category..) etc of the movie as mentioned by category
        """

        if id.startswith('http'):
            url=id
            if category and EXPANDS.index("@" + category) >= 0:
                url = "%s/%s" % (url, category)
            return self._request('get', url).json()
        else:
            raise NetflixError("The id should be like: http://api.netflix.com/catalog/movies/60000870")

    def search_people(self, term, start_index=None, max_results=None):
        """search for people in the catalog by their name or a portion of their name.

        url: /catalog/people

        :param term: The term in the person's name to search for in the catalog.
        :param start_index:  (optional) The zero-based offset into the list that results from the query.
        :param max_results: (optinoal) The maximum number of results to return. 

        :Retruns:
            Returns results that include catalog title entries for titles that involve people that match 
            the specified name. Results also include references to person details.
        """

        url_path = '/catalog/people'
        data = {'term': term,
                     'start_index': start_index, 'max_results': max_results}
        return self._request("get", url_path, data).json()

    def get_person(self, id):
        """ You can retrieve detailed information about a person in the Catalog, using that person's ID,
        that includes a biography, featured titles, and a complete list of titles

        url: /catalog/people/person_id

        :param id: This is the id that is returned for the person in ``search_people`` call (id looks like
            ``http://api.netflix.com/catalog/people/185930``

        :returns: The dict object containng details of the person

        """
        if id.startswith('http'):
            url=id
            return self._request('get', url).json()
        else:
            raise NetflixError("The id should be like: http://api.netflix.com/catalog/people/185930")


    def get_user(self, user_id, user_token, user_token_secret):
        """ Returns the user object, which could then be used to make further user specific calls 

        url: /users/current
        :param user_id: The user id as received using the ``get_access_token()`` method
        :param user_token: The user token as received using the ``get_access_token()`` method
        :param user_token_secret: The user token secret as received using the ``get_user_token()`` method

        :returns: ``dict`` object containg user information. The return object is different for `v1` and `v2`
        """
        user = User(self, user_id, user_token, user_token_secret)
        return user


    def _assert_authorized(self):
        if not self._user_credential_set:
            raise NetflixAuthRequiredError("User is not authorized")

    @staticmethod
    def _append_param(url, parameters):
        """ Append additional query parameters to an existing url
        
        :param url: The URL to which append additional query parameters
        :param parameters: The parameters to add
        
        :returns:
            (``string``) The new url
        :rtype: string
        """

        url_parts = list(urlparse(url))
        query = dict(parse_qsl(url_parts[4]))
        query.update(parameters)
        url_parts[4] = urllib.urlencode(query)
        url = urlunparse(url_parts)
        return url

    def _log(self, msg):
        try:
            if self._logger:
                self._logger.write('%s   %s\n' % (
                    datetime.now().isoformat(), msg))
        except:
            print "Caught exception [%s] while trying to log msg, \
                                  ignored: %s" % (sys.exc_info()[0], msg)

    def _request(self, method, url, data={}, headers={}, client=None, stream=False):
        """
        """
        if self._api_version == 2.0:
            data['v'] = 2.0

        if not data or 'output' not in data:
            data['output'] = 'json'

        # Remove parameters with value None
        for k in data.keys():
            if data[k] is None:
                del data[k]

        if not url.startswith('http'):
            url = "%s%s" % (BASE_URL, url)

        if not client:
            client = self._client

        if method is "get":
            r = client.request(method, url, params=data, headers=headers, allow_redirects=True, stream=stream)
        else:
            r = client.request(method, url, data=data, headers=headers, allow_redirects=True, stream=stream)

        self._log((r.request.method, r.url, r.status_code))
        if r.status_code < 200 or r.status_code >= 300:
            error = {}
            try:
                error = json.loads(r.content or r.text)
            except:
                self._log("Couldn't jsonify error response: %s" % (r.content or r.text))
            raise NetflixError("Error fetching url: {0}. Code: {1}. Error: {2} "
                    .format(r.url, r.status_code, r.content), error)
        return r


class NetflixAPIV1(_NetflixAPI):
    """ Provides functional interface to Netflix V1 REST api"""

    def __init__(self, appname, consumer_key, consumer_secret, logger=None):
        """ The main class for accessing the Netflix REST API v1.0 http://developer.netflix.com/docs/REST_API_Reference
        It provides all the methods needed to access the resources exposed by netflix. Netflix has now released version 2.0
        http://developer.netflix.com/page/Netflix_API_20_Release_Notes which is backward incompatible. So going forward netflix
        may *deprectate* the version 1.0 APIs. So it is recommended to use version 2.0 API instead 

        :param appname: The Application name as registered in Netflix Developer 
            website <http://developer.netflix.com/apps/mykeys>
        :param consumer_key: The consumer key as registered in Netlflix Developer website
        :param consumer_secret: The consumer secret as registered in Netflix Developer website
            three legged authentication 
        :param logger: (Optional) The stream object to write log to. Nothing is logged if `logger` is `None`
        """
        super(NetflixAPIV1, self).__init__(appname, consumer_key, consumer_secret, logger)
        self._api_version = 1.0

    def search_titles(self, term, start_index=0, max_results=25):
        """Use the catalog titles resource to search the netflix movie catalog(includes all medium)
        for titles of movies and television series. 

        url: /catalog/titles

        :param term: The word or term to search the catalog for. The Netflix
            API searches the title and synopses of catalog titles for a match.
        :param start_index:  (optional) The zero-based offset into the list that results
            from the query. By using this with the max_results parameter, user
        :param max_results: (optinoal) The maximum number of results to return. 
            This number cannot be greater than 100. If you do not specify 
            `max_results`, the default value is 25. can request successive pages of search results.

        :Returns:
            Returns the matching titles as a series of `catalog_title` records in relevance order, 
            and the total number of results in `results_per_page`.
        """
        return super(NetflixAPIV1, self).search_titles(term, start_index=start_index, max_results = max_results)

    def title_autocomplete(self, term, start_index=None, max_results=None):
        """ Searches the catalog for  for movies and television series whose "short" 
        titles match a partial search text. You can then pass the title names that 
        Netflix API returns from this request to the title search methods in order 
        to conduct the actual title search. You can only autocomplete titles 
        (not other items, like names of actors).

        url: /catalog/titles/autocomplete

        :param term: The string to look for partial match in short titles
        :param start_index:  (optional) The zero-based offset into the list that results from the query.
        :param max_results: (optinoal) The maximum number of results to return. 

        :Returns:
             Returns a list of movie and television title names that match your partial search text. 
        """
        return super(NetflixAPIV1, self).title_autocomplete(term, start_index=start_index,
                                                  max_results=max_results)
    def get_movie_by_title(self, movie_title):
        """ Returns the first movie that matches the title

        :param movie_title: The exact movie name
        :returns: the movie object matching the title"""

        search_result = self.search_titles(movie_title)
        for movie in search_result['catalog_titles']['catalog_title']:
            title = movie['title']['regular']
            if movie_title.lower() == title.lower():
                self._log("Found movie: '%s' id: '%s'" % (title, movie['id']))
                return movie
        return None

    def get_catalog(self, catalog_type='index', chunk_size=4096, raw=False):
        """Retrieve a complete index of all instant-watch titles in the Netflix catalog

        :param catalog_type: The type of catalog to fetch; see :py:data:`CATALOG_TYPES_V1`

        URLs: 
            /catalog/titles/index
            /catalog/titles/streaming
            /catalog/titles/dvd

        :Returns:
            Returns an iter object which can be written to disk etc
        """
        if not CATALOG_TYPES_V1.index(catalog_type):
            raise NetflixError("Invalid catalog type")

        url_path = '/catalog/titles/%s' % catalog_type
        resp = self._request("get", url_path, headers={'Accept-Encoding': 'gzip'}, data={'output': None}, stream=True)
        if raw:
            return resp.raw
        return resp.iter_content(chunk_size)

class NetflixAPIV2(_NetflixAPI):
    """ Provides functional interface to Netflix V2 REST api"""

    def __init__(self, appname, consumer_key, consumer_secret, access_token=None, logger=None):
        """ The main class for accessing the Netflix REST API v2.0 http://developer.netflix.com/page/Netflix_API_20_Release_Notes
        It provides all the methods needed to access the resources exposed by netflix. The version 2.0 of the API 
        is backward incompitable. So going forward netflix may *deprectate* the version 1.0 APIs. So it is 
        recommended to use this class for accessing netflix API.

        :param appname: The Application name as registered in Netflix Developer 
            website <http://developer.netflix.com/apps/mykeys>
        :param consumer_key: The consumer key as registered in Netlflix Developer website
        :param consumer_secret: The consumer secret as registerde in Netflix Developer website
        :param logger: (Optional) The stream object to write log to. Nothing is logged if `logger` is `None`
        """
        super(NetflixAPIV2, self).__init__(appname, consumer_key, consumer_secret, logger)
        self._api_version = 2.0

    def search_titles(self, term, filter=None, expand=None, start_index=0, max_results=25):
        """Use the catalog titles resource to search the netflix movie catalog(includes all medium)
        for titles of movies and television series. 

        url: /catalog/titles

        :param term: The word or term to search the catalog for. The Netflix
            API searches the title and synopses of catalog titles for a match.
        :param filter: The filter could be either the string `"instant"` or `"disc"`
        :param expand: The expand parameter instructs the API to expand the ``expand``
            (``"@title", "@box_art"``, see :py:data:`EXPANDS`)  part of data and include that data inline in the element
        :param start_index:  (optional) The zero-based offset into the list that results
            from the query. By using this with the ``max_results`` parameter, user
        :param max_results: (optinoal) The maximum number of results to return. 
            This number cannot be greater than 100. Can request successive pages of search results.

        :Returns:
            Returns the matching titles as a series of ``catalog_title`` records in relevance order, 
            and the total number of results in ``results_per_page``.
        :rtype: dict
        """
        return super(NetflixAPIV2, self).search_titles(term, filter=filter, expand=expand, start_index=start_index,
                                                  max_results = max_results)

    def title_autocomplete(self, term, filter=None, start_index=None, max_results=None):
        """ Searches the catalog for  for movies and television series whose "short" 
        titles match a partial search text. You can then pass the title names that 
        Netflix API returns from this request to the title search methods in order 
        to conduct the actual title search. You can only autocomplete titles 
        (not other items, like names of actors).

        url: /catalog/titles/autocomplete

        :param term: The string to look for partial match in short titles
        :param start_index:  (optional) The zero-based offset into the list that results from the query.
        :param filter: (optional)The filter could be either the string `"instant"` or `"disc"`
        :param max_results: (optinoal) The maximum number of results to return. 

        :Returns:
             Returns a list of movie and television title names that match your partial search text. 
        """
        return super(NetflixAPIV2, self).title_autocomplete(term, filter=filter, start_index=start_index,
                                                  max_results = max_results)
    def get_movie_by_title(self, movie_title, filter=None):
        """ Returns the first movie that matches the title

        :param movie_title: The exact movie name
        :param filter: The filter
        :returns: the movie object matching the title"""

        search_result = self.search_titles(movie_title, filter=filter)
        for movie in search_result['catalog']:
            title = movie['title']
            if movie_title.lower() == title.lower():
                self._log("Found movie: '%s' id: '%s'" % (title, movie['id']))
                return movie
        return None

    def get_catalog(self, catalog_type='full', chunk_size=4096, raw=False):
        """Retrieve a complete index of all instant-watch/dvd titles in the Netflix catalog

        :param catalog_type: The type of catalog to fetch; see :py:data:`CATALOG_TYPES_V2`

        URLs:
            /catalog/titles/full
            /catalog/titles/streaming
            /catalog/titles/dvd

        :Returns:
            Returns an iter object which can be written to disk etc
        """
        try:
            is_valid = CATALOG_TYPES_V2.index(catalog_type)
        except ValueError:
            raise NetflixError("Invalid catalog type")

        url_path = '/catalog/titles/%s' % catalog_type
        resp = self._request("get", url_path, headers={'Accept-Encoding': 'gzip'}, data={'output': None}, stream=True)
        if raw:
            return resp.raw
        return resp.iter_content(chunk_size)

class User:
    def __init__(self, netflix_client, user_id, access_token, access_token_secret):
        """Don't use this constructor directly, use :py:meth:`~NetflixAPIV2.get_user()` instead

        :param netflix_client: The Netflix client
        :param access_token: (Optional) User access token obtained using OAuth three legged authentication 
        :param access_token_secret: (Optional) User access token  secret obtained using OAuth 
            three legged authentication 
        """

        if not access_token:
            raise NetflixError("access_token cannot be null/empty")
        if not access_token_secret:
            raise NetflixError("access_token_secret cannot be null/empty")

        self._netflix_client = netflix_client
        self._access_token = access_token.strip()
        self._access_token_secret = access_token_secret.strip()
        oauth = OAuth1(netflix_client._consumer_key, client_secret=netflix_client._consumer_secret,  resource_owner_key=self._access_token,
            resource_owner_secret=self._access_token_secret, signature_type='query')
        self._client = requests.Session()
        self._client.auth = oauth
        self.id = user_id

    def get_details(self):
        """Returns information about the subscriber with the specified user ID
        url: /users/user_id
        """
        url_path = '/users/' + self.id
        return self._request('get', url_path ).json()

    def get_feeds(self):
        """Netflix API returns a list of URLs of all feeds available for the specified user.
        url: /users/user_id/feed
        """

        url_path = '/users/' + self.id + "/feeds"
        return self._request('get', url_path).json()

    def get_title_states(self, title_refs=None):
        """returns a series of records that indicate the relationship between the subscriber and one or more titles.
        url: /users/user_id/title_states

        :param title_refs: list of catalog title URLs
        :returns: relationship between the subscriber and the movies he has added to qeueu
        """

        data = {}
        if title_refs:
            data = {"title_refs" : ",".join(title_refs)}
        url_path = '/users/' + self.id + "/feeds"
        return self._request('get', url_path, data=data).json()

    def get_queues(self, expand=None, sort_order=None, start_index=None, 
                   max_results=None, updated_min=None):
        """Returns the contents of a subscriber's queue.
        url: /users/userID/queues

        :param sort_order: One of `queue_sequence`, `date_added` or `alphabetical`. Default is `queue_sequence`
        :param start_index: The zero-based offset into the results for the query
        :param max_results: Maximum number of results you want.
        :param updated_min: Only results whose updated time is greater than this would be returned. 
            Unix epoch time format or RFC 3339 format
        :returns: Subscriber's queue
        """

        return self._request_queue("get", '/users/' + self.id + "/queues",
                          expand, sort_order, start_index, max_results, updated_min)


    def get_queues_instant(self, expand=None, sort_order=None, start_index=None, 
                   max_results=None, updated_min=None):
        """Returns details about a subscriber's instant watch queue

        url: /users/userID/queues/instant

        :param sort_order: One of `queue_sequence`, `date_added` or `alphabetical`. Default is `queue_sequence`
        :param start_index: The zero-based offset into the results for the query
        :param max_results: Maximum number of results you want.
        :param updated_min: Only results whose updated time is greater than this would be returned. 
            Unix epoch time format or RFC 3339 format
        :returns: Subscriber's instant-watch queue
        """
        return self._request_queue("get", '/users/' + self.id + "/queues/instant",
                                    expand, sort_order, start_index, max_results, updated_min)

    def get_queues_disc(self, expand=None, sort_order=None, start_index=None, 
                   max_results=None, updated_min=None):
        """Returns details about a subscriber's disc queue
        url: /users/userID/queues/disc

        :param sort_order: One of `queue_sequence`, `date_added` or `alphabetical`. Default is `queue_sequence`
        :param start_index: The zero-based offset into the results for the query
        :param max_results: Maximum number of results you want.
        :param updated_min: Only results whose updated time is greater than this would be returned. 
            Unix epoch time format or RFC 3339 format
        :returns: Subscriber's disc queue
        """

        return self._request_queue("get", '/users/' + self.id + "/queues/disc",
                                    expand, sort_order, start_index, max_results, updated_min)

    def add_queue_instant(self, title_ref, position, etag):
        """These resources automatically add the title to the saved or available queue, 
        depending on the title's availability. Use :py:meth:`~User.get_title_states`
        to see the status of the movie in your queue

        url: /users/userID/queues/instant

        :param title_ref: The catalog title to be added to the queue.
        :param position: The position (positions start with "1") in the queue at which to 
            insert or move the title.
        :param etag: The queue's ETag value that Netflix API returned the last time you 
            accessed the queue. Use this for concurrency control.

        :returns:  If it is successful, Netflix API returns the queue entries that got
            created or modified with your POST request. If this request involved moving a title within 
            a queue, the API returns only that queue item with its updated position. The API throws an error 
            if a title is not available. The POST operation fails if the queue has been updated since the time 
            you retrieved the ETag value that you passed in. Each successful (or partially successful) POST 
            response includes a new ETag value that you can then use in subsequent requests.
        """
        data = {'title_ref': title_ref, 'position': position, 'etag': etag}
        return self._request_queue("post", '/users/%s/queues/instant' % self.id)

    def get_resource(self, url, data={}):
        return self._request("get", url, data=data)

    def get_queues_instant_available(self, entry_id=None, sort_order=None, 
                                    start_index=None, max_results=None, updated_min=None):
        """Retrieves availability details about the subscriber's instant-watch queue

        url: /users/userID/queues/instant/available

        :param sort_order: One of `queue_sequence`, `date_added` or `alphabetical`. Default is `queue_sequence`
        :param start_index: The zero-based offset into the results for the query
        :param max_results: Maximum number of results you want.
        :param updated_min: Only results whose updated time is greater than this would be returned. 
            Unix epoch time format or RFC 3339 format
        :returns: Subscriber's availability details of instant-watch queue
        """

        queue_path = '/users/%s/queues/instant/available' % self.id
        if entry_id:
            queue_path += '/' + entry_id
        return self._request_queue("get", queue_path,
                None, sort_order, start_index, max_results, updated_min)

    def delete_queues_instant_available(self, entry_id):
        """  deletes the specified entry from the subscriber's instant watch queue.
        url: /users/userID/queues/instant/available/entryID

        :param entry_id: the entry id
        """
        queue_path = '/users/%s/queues/instant/available/%s' %  (self.id, entry_id)
        return self._request_queue('delete', queue_path)

    def get_queues_instant_saved(self, expand=None, entry_id=None, sort_order=None, 
                                    start_index=None, max_results=None, updated_min=None):
        """Returns the saved status of an entry in a subscriber's instant-watch queue.
        url: /users/userID/queues/instant/saved

        :param sort_order: One of `queue_sequence`, `date_added` or `alphabetical`. Default is `queue_sequence`
        :param start_index: The zero-based offset into the results for the query
        :param max_results: Maximum number of results you want.
        :param updated_min: Only results whose updated time is greater than this would be returned. 
            Unix epoch time format or RFC 3339 format
        """

        queue_path = '/users/%s/queues/instant/saved' % self.id
        if entry_id:
            queue_path += '/' + entry_id
        return self._request_queue("get", queue_path,
                                    expand, sort_order, start_index, max_results, updated_min)

    def delete_queue_instant_saved(self, entry_id):
        """ Deletes the specified entry from the subscriber's instant-watch queue.
        url: /users/userID/queues/instant/saved/entryID

        :param entry_id: The entry_id"""

        queue_path = '/users/%s/queues/instant/saved/%s' %  (self.id, entry_id)
        return self._request_queue('delete', queue_path)

    def _request_queue(self, method, queue_path, expand=None, sort_order=None, start_index=None, 
                   max_results=None, updated_min=None):
        data = {'start_index' : start_index, 'max_results': max_results, 'updated_min': updated_min}
        if sort_order and SORT_ORDER.index(sort_order):
            data['sort'] = sort_order
        if expand and EXPANDS.index(expand) >= 0:
            data['expand'] = expand
        return self._request(method, queue_path, data=data).json()

    def get_rental_history(self, type=None, start_index=None, max_results=None, updated_min=None):
        """ Get a list of titles that reflect a subscriber's viewing history
            Note: This API to be obsolete on 15th Sept, 2012 http://goo.gl/AYOlt

        url: /users/userID/rental_history

        :param type: type of rental history, "watched", "shipped" etc, see :py:data:`RENTAL_HISTORY_TYPE`
        :param start_index: The zero-based offset into the results for the query
        :param max_results: Maximum number of results you want.
        :param updated_min: Only results whose updated time is greater than this would be returned. 
            Unix epoch time format or RFC 3339 format
        """
        url_path = '/users/%s/rental_history' % self.id
        if type and RENTAL_HISTORY_TYPE.index(type) >= 0:
            url_path += '/%s' % type
        data = {'start_index' : start_index, 'max_results': max_results, 'updated_min': updated_min}
        return self._request('get', url_path, data=data).json()


    def get_rating(self, title_refs):
        """Returns a list of movie or television series ratings for the designated subscriber. 
        If available, the subscriber's actual ratings are returned; otherwise, the resource 
        returns the Netflix-predicted ratings.
        url: /users/userID/ratings/title 

        :param title_refs: List of title ids
        :returns: List of rating of given titles 
        """
        return self._request_ratings('get', '/users/%s/ratings/title' % self.id, title_refs)

    def get_actual_rating(self, title_refs):
        """Get rating for titles given by the subscriber
        url: /users/userID/ratings/title/actual

        :param title_refs: List of title ids
        """
        return self._request_ratings('get', '/users/%s/ratings/title/actual' % self.id, title_refs)

    def add_my_rating(self, title_ref, rating):
        """Add user's custom rating
        url: /users/userID/ratings/title/actual

        :param title_ref: List of title ids
        :param rating: the rating
        """
        data = {'rating': rating, 'title_ref': title_ref}
        return self._request_ratings('post', '/users/%s/ratings/title/actual' % self.id, data=data)

    def get_my_rating(self, rating_id):
        """Get particular rating that uesr has already given using the rating id
        url: /users/userID/ratings/title/actual/ratingID

        :param rating_id: the integer rating id"""

        return self._request('get', '/users/%s/ratings/title/actual/%s' % (self.id, rating_id), data={}).json()

    def update_my_rating(self, rating_id, rating):
        """Udate particular rating that uesr has already given using the rating id
        url: /users/userID/ratings/title/actual/ratingID

        :param rating_id: the integer rating id
        :param rating: the rating
        """
        data = {'rating': rating}
        return self._request_ratings('put', '/users/%s/ratings/title/actual/%s' % (self.id, rating_id), data=data)

    def get_predicted_ratings(self, title_refs):
        """ Get predicted rating for given titles
        url: /users/userID/ratings/title/predicted

        :param title_refs: List of title ids
        """
        return self._request_ratings('get', '/users/%s/ratings/title/predicted' % self.id, title_refs)

    def _request_ratings(self, method, url_path, title_refs=[], data = {}):
        if not data:
            data['title_refs'] =  ','.join(title_refs)
        return self._request(method, url_path, data=data).json()

    def get_recommendations(self, start_index=None, max_results=None):
        """Get Netflix's catalog title recommendations for a subscriber, based on a subscriber's viewing history.
        url: /users/userID/recommendations

        :param start_index: The zero-based offset into the results for the query
        :param max_results: Maximum number of results you want.
        """
        data = {'start_index': start_index, 'max_results': max_results}
        return self._request('get', '/users/%s/recommendations' % self.id, data=data).json()


    def _request(self, method, url, data={}, headers={}):
        return self._netflix_client._request(method, url, data, headers, client=self._client)

