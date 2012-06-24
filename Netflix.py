""" Library for accessing the REST API from Netflix
"""

import sys
import os.path
import requests
from oauth_hook import OAuthHook
import pprint
import time
from datetime import datetime
from urlparse import urlparse, parse_qs, parse_qsl, urlunparse
import urllib
import json

__version__ = "0.1.1"

BASE_URL= 'http://api.netflix.com'
REQUEST_TOKEN_URL = 'http://api.netflix.com/oauth/request_token'
ACCESS_TOKEN_URL = 'http://api.netflix.com/oauth/access_token'
AUTHORIZATION_URL = 'https://api-user.netflix.com/oauth/authenticate'
NETFLIX_FILTER = {'disc': 'http://api.netflix.com/categories/title_formats/disc',
                  'instant': 'http://api.netflix.com/categories/title_formats/instant'}
EXPANDS = ["@title", "@box_art", "@synopsis", "@short_synopsis", "@format_availability", "@screen_formats",
          "@cast", "@directors", "@languages_and_audio", "@awards", "@similars", "@bonus_materials",
          "@seasons", "@episodes", "@discs"]
""" Allowed expand strings while calling the titles api"""

SORT_ORDER = ["queue_sequence", "date_added", "alphabetical"]
""" Allowed sort order while retrieveing queues"""



class NetflixError(Exception):
    """ Error thrown if the netflix api throws http error"""
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
        self._consumer_name = appname
        self._consumer_key = consumer_key
        self._consumer_secret = consumer_secret

        OAuthHook.consumer_key = consumer_key
        OAuthHook.consumer_secret = consumer_secret
        self._logger = logger

        oauth_hook = OAuthHook()
        self._client = requests.session(hooks={'pre_request': oauth_hook})



    def get_request_token(self, use_OOB = True):
        """Obtains the request token/secret and the authentication URL

        :param use_OOB: (Optional) If set to false the oauth out-of-bound authentication is used
            which requires the user to go to nerflix website and get the verfication code
            and provide here

        :Returns:
            Returns the triplet ``(request_token, request_token_secret , url)``
        :rtype: (string, string, string)
        """

        # Step 1: Obtain the request Token
        request_oauth_hook = OAuthHook()
        client = requests.session(hooks={'pre_request': request_oauth_hook})
        if use_OOB:
            data = {'oauth_callback': 'oob'}
        else:
            data = {}
        response = client.post(REQUEST_TOKEN_URL, data=data)
        response = parse_qs(response.content)
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
        return (request_token, request_secret, auth_url )

    def get_access_token(self, request_token, request_token_secret, oauth_verification_code = None):
        """Obtains the access token/secret, given:

            - The ``request_token`` and ``request_token_secret`` has been authorized  by visiting the netflix authorization URL by user
            - The user has obtained the verification code (when ``use_OOB`` was set in ``get_request_token`` from netflix website)

        :param request_token: The request token obtained using :meth: get_request_token 
        :param request_token_secret: The request token secret obtained using :py:meth:`~NetflixAPI.get_request_token`
        :param oauth_verification_code: (Optional) The verification code obtained from netflix website, if ``use_OOB`` 
            was set to ``True`` in :py:meth:`~NetflixAPIV2.get_request_token`

        :Returns:
            Returns the pair ``(access_token, access_token_secret)``
        :rtype: (string, string)
        """
        # Step 3: Obtain access token
        access_oauth_hook = OAuthHook(request_token, request_token_secret)
        client = requests.session( hooks={'pre_request': access_oauth_hook})
        params = {'oauth_token': request_token.key}

        if oauth_verification_code:
            params['oauth_verifier'] = oauth_verification_code
        response = client.post(ACCESS_TOKEN_URL, params)

        response = parse_qs(response.content)
        return (response['oauth_token'][0], response['oauth_token_secret'][0])

    def search_titles(self, term, filter=None, expand=None, start_index=None, max_results=None):
        """Use the catalog titles resource to search the netflix movie catalog(includes all medium)
        for titles of movies and television series. 

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
        if expand and EXPANDS.index(expand):
            data['expand'] = expand
        return self._request("get", url_path, data).json

    def get_catalog(self):
        """Retrieve a complete index of all instant-watch titles in the Netflix catalog

        :Returns:
            Returns an iter object which can be written to disk etc
        """
        url_path = '/catalog/titles/index'
        r = self._request("get", url_path, headers={ 'Accept-Encoding': 'gzip'})
        return r.iter_content

    def title_autocomplete(self, term, filter=None, start_index=None, max_results=None):
        """ Searches the catalog for  for movies and television series whose "short" 
        titles match a partial search text. You can then pass the title names that 
        Netflix API returns from this request to the title search methods in order 
        to conduct the actual title search. You can only autocomplete titles 
        (not other items, like names of actors).

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
        return self._request("get", url_path, data).json

    def get_resource(self, url):
        self._log(("get", url))
        data = {'output': 'json'}

        info = self._request('get', url, data=data)
        return info.json

    def get_title(self, id,  category=None):
        """ Retrieve details for specific catalog title

        :param id: This is the id that is returned for movies in ``search_movie`` call (id looks like
            ``http://api.netflix.com/catalog/titles/movies/60000870``)
        :param category: The expand parameter instructs the API to get (``"title", "box_art"``, 
            see :py:data:`EXPANDS` without the `@` though)  information of the movie

        :returns: 
            The detail of the movie **OR** (award/category..) etc of the movie as mentioned by category
        """

        if 'http' in id:
            url=id
            if category and EXPANDS.index("@" + category):
                url = "%s/%s" % (url, category)
            return self._request('get', url).json
        else:
            raise NetflixError("The id should be like: http://api.netflix.com/catalog/people/185930")

    def search_people(self, term, start_index=None, max_results=None):
        """search for people in the catalog by their name or a portion of their name.

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
        return self._request("get", url_path, data).json

    def get_person(self, id):
        """ You can retrieve detailed information about a person in the Catalog, using that person's ID,
        that includes a biography, featured titles, and a complete list of titles

        :param id: This is the id that is returned for the person in ``search_people`` call (id looks like
            ``http://api.netflix.com/catalog/people/185930``

        :returns: The dict object containng details of the person

        """
        if 'http' in id:
            url=id
            return self.get_resource(url)
        else:
            raise NetflixError("The id should be like: http://api.netflix.com/catalog/people/185930")


    def get_user(self, user_token, user_token_secret):
        """ Returns the user object, which could then be used to make further user specific calls 

        :param id: Retrieves information about the user whose ``id`` is given. If ``id`` is not given
            the current user's infomation is retrieved

        :returns: ``dict`` object containg user information. The return object is different for `v1` and `v2`
        """
        user = User(self, user_token, user_token_secret)
        return user


    def _assert_authorized(self):
        if not self._user_credential_set:
            raise NetflixAuthRequiredError("User is not authorized")

    @staticmethod
    def get_integer_id(url):
        """ This method can find the id and the type of resource from a netflix URL"""
        raise NotImplementedError

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

    def _request(self, method, url, data={}, headers={}, client=None):
        """
        """
        if(self._api_version == 2.0):
            data['v'] = 2.0

        if not data or 'output' not in data:
            data['output'] = 'json'

        # Remove parameters with value None
        for k in data.keys():
            if data[k] is None:
                del data[k]

        if not url.startswith('http'):
            url = "%s%s" % (BASE_URL, url)

        config = {}
        if self._logger:
            config['verbose'] = self._logger

        if not client:
            client = self._client

        r = client.request(method, url, data=data, config=config, headers=headers)
        self._log((r.request.method, r.url, r.status_code))
        if(r.status_code < 200 or r.status_code >= 300):
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

        :param term: The string to look for partial match in short titles
        :param start_index:  (optional) The zero-based offset into the list that results from the query.
        :param max_results: (optinoal) The maximum number of results to return. 

        :Returns:
             Returns a list of movie and television title names that match your partial search text. 
        """
        return super(NetflixAPIV1, self).title_autocomplete(term, start_index=start_index,
                                                  max_results=max_results)


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

        :param term: The string to look for partial match in short titles
        :param start_index:  (optional) The zero-based offset into the list that results from the query.
        :param filter: (optional)The filter could be either the string `"instant"` or `"disc"`
        :param max_results: (optinoal) The maximum number of results to return. 

        :Returns:
             Returns a list of movie and television title names that match your partial search text. 
        """
        return super(NetflixAPIV2, self).title_autocomplete(term, filter=filter, start_index=start_index,
                                                  max_results = max_results)


class User:
    def __init__(self, netflix_client, access_token, access_token_secret, id=None):
        """"
        :param access_token: (Optional) User access token obtained using OAuth three legged authentication 
        :param access_token_secret: (Optional) User access token  secret obtained using OAuth 
            three legged authentication 
        """
        """ Sets the user access token and secret for future calls
        Must be set for calls that require a user to be authenticated"""

        if not access_token:
            raise NetflixError("access_token cannot be null/empty")
        if not access_token_secret:
            raise NetflixError("access_token_secret cannot be null/empty")

        oauth_hook = OAuthHook(access_token, access_token_secret)
        self._netflix_client = netflix_client
        self._client = requests.session(hooks={'pre_request': oauth_hook})
        self._access_token = access_token
        if not id:
            user = self._request('get', "/users/current").json
            if 'resource' in user:
                url = user['resource']['link']['href']
            elif 'http://schemas.netflix.com/user.current' in user:
                url = user['http://schemas.netflix.com/user.current']
            id = url.split('/')[-1]
        self.id = id

    def get_details(self):
        """Returns information about the subscriber with the specified user ID"""
        url_path = '/users/' + self.id
        return self._request('get', url_path ).json

    def get_feeds(self):
        """Netflix API returns a list of URLs of all feeds available for the specified user."""

        url_path = '/users/' + self.id + "/feeds"
        return self._request('get', url_path).json

    def get_title_states(self, title_refs=None):
        """returns a series of records that indicate the relationship between the subscriber and one or more titles."""
        data = {}
        if title_refs:
            data = {"title_refs" : ",".join(title_refs)}
        url_path = '/users/' + self.id + "/feeds"
        return self._request('get', url_path, data=data).json

    def get_queues(self, sort_order=None, start_index=None, 
                   max_results=None, updated_min=None):
        """Returns the contents of a subscriber's instant-watch queue."""
        return self._request_queue("get", '/users/' + self.id + "/queues", 
                          sort_order, start_index, max_results, updated_min)


    def get_queues_instant(self, sort_order=None, start_index=None, 
                   max_results=None, updated_min=None):
        """Returns details about a subscriber's instant watch queue"""
        return self._request_queue("get", '/users/' + self.id + "/queues/instant",
                          sort_order, start_index, max_results, updated_min)

    def get_queues_disc(self, sort_order=None, start_index=None, 
                   max_results=None, updated_min=None):
        """Returns details about a subscriber's disc queue"""
        return self._request_queue("get", '/users/' + self.id + "/queues/disc",
                          sort_order, start_index, max_results, updated_min)

    def add_queue_instant(self, title_ref, position, etag):
        """These resources automatically add the title to the saved or available queue, 
        depending on the title's availability. Use :py:meth:`~User.get_title_states`
        to see the status of the movie in your queue

        :param title_ref: The catalog title to be added to the queue.
        :param position: The position (positions start with "1") in the queue at which to 
            insert or move the title.
        :param etag: The queue's ETag value that Netflix API returned the last time you 
            accessed the queue. Use this for concurrency control.

        :returns: If your request is successful, Netflix API returns the queue entries that got
        created or modified with your POST request. If this request involved moving a title within 
        a queue, the API returns only that queue item with its updated position. The API throws an error 
        if a title is not available. The POST operation fails if the queue has been updated since the time 
        you retrieved the ETag value that you passed in. Each successful (or partially successful) POST 
        response includes a new ETag value that you can then use in subsequent requests.
        """
        data = {'title_ref': title_ref, 'position': position, 'etag': etag}
        return self._request_queue("post", '/users/%s/queues/instant' % self.id,
                          sort_order, start_index, max_results, updated_min)

    def get_queues_instant_available(self, entry_id=None, sort_order=None, 
                                    start_index=None, max_results=None, updated_min=None):
        """Retrieves details about the entry from the subscriber's instant-watch queue"""

        queue_path = '/users/%s/queues/instant/available' % self.id
        if entry_id:
            queue_path += '/' + entry_id
        return self._request_queue("get", queue_path,
                sort_order, start_index, max_results, updated_min)

    def delete_queues_instant_available(self, entry_id):
        queue_path = '/users/%s/queues/instant/available/%s' %  (self.id, entry_id)
        return self._request_queue('delete', queue_path)

    def get_queues_instant_saved(self, entry_id=None, sort_order=None, 
                                    start_index=None, max_results=None, updated_min=None):
        """Returns the saved status of an entry in a subscriber's instant-watch queue."""

        queue_path = '/users/%s/queues/instant/saved' % self.id
        if entry_id:
            queue_path += '/' + entry_id
        return self._request_queue("get", queue_path,
                sort_order, start_index, max_results, updated_min)

    def delete_queue_instant_saved(self, entry_id):
        queue_path = '/users/%s/queues/instant/saved/%s' %  (self.id, entry_id)
        return self._request_queue('delete', queue_path)

    def _request_queue(self, method, queue_path, sort_order=None, start_index=None, 
                   max_results=None, updated_min=None):
        data = {'start_index' : start_index, "max_results": max_results, "updated_min": updated_min}
        if sort_order and SORT_ORDER.index(sort_order):
            data['sort'] = sort_order
        return self._request(method, queue_path, data=data).json

    def get_rental_history(self, type=None, start_index=None, max_results=None, updated_min=None):
        url_path = '/users/' + self.id + '/rental_history'
        if type:
            url_path += '/watched'
        return self._request('get', url_path).json


    def get_rating(self, title_refs):
        """Returns a list of movie or television series ratings for the designated subscriber. 
        If available, the subscriber's actual ratings are returned; otherwise, the resource 
        returns the Netflix-predicted ratings.

        :param title_refs: List of title ids
        :returns: List of rating of given titles 
        """
        return self._request_ratings('get', '/users/%s/ratings/title' % self.id, title_refs)

    def get_actual_rating(self, title_refs):
        return self._request_ratings('get', '/users/%s/ratings/title/actual' % self.id, title_refs)

    def add_my_rating(self, title_ref, rating):
        data = {'rating': rating, 'title_ref': title_ref}
        return self._request_ratings('post', '/users/%s/ratings/title/actual' % self.id, data=data)

    def get_my_rating(self, rating_id):
        # Broken
        return self._request('get', '/users/%s/ratings/title/actual/%s' % (self.id, rating_id), data={}).json

    def update_my_rating(self, rating_id, rating):
        # Broken
        data = {'rating': rating}
        return self._request_ratings('put', '/users/%s/ratings/title/actual/%s' % (self.id, rating_id), data=data)

    def get_predicted(self):
        return self._request('get', '/users/%s/ratings/title/predicted' % self.id).json

    def _request_ratings(self, method, url_path, title_refs=[], data = {}):
        if not data:
            data['title_refs'] =  ','.join(title_refs)
        return self._request(method, url_path, data=data).json

    def get_reccomendations(self, start_index=None, max_results=None):
        data = {'start_index': start_index, 'max_results': max_results}
        return self._request('get', '/users/%s/recommendations' % self.id, data=data).json


    def _request(self, method, url, data={}, headers={}):
        return self._netflix_client._request(method, url, data, headers, client=self._client)

