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



class NetflixError(Exception):
    pass

class NetflixAuthRequiredError(Exception):
    """Exception thrown when the netflix client is not provided ``access_token`` and ``access_token_secret`` but
    a protcted call is made"""


class OAuthToken(object):
    def __init__(self, key, secret):
        self.key, self.secret = key, secret


class NetflixUser():

    def get_data(self):
        access_token=self.access_token

        if not isinstance(access_token, oauth.o_auth_token):
            access_token = oauth.OAuthToken( 
                                    access_token['key'], 
                                    access_token['secret'] )

        request_url = '/users/%s' % (access_token.key)
        parameters = { 'output': 'json' }

        info = simplejson.loads( self.client._get_resource( 
                                    request_url,
                                    parameters = parameters,
                                     token=access_token ) )
        self.data = info['user']
        return self.data

    def get_info(self, field):
        access_token = self.access_token

        if not self.data:
            self.get_data()

        fields = []
        url = ''
        parameters = { 'output': 'json' }
        for link in self.data['link']:
            fields.append(link['title'])
            if link['title'] == field:
                url = link['href']

        if not url:
            error_string =           "Invalid or missing field.  " + \
                                    "Acceptable fields for this object are:"+ \
                                    "\n\n".join(fields)
            print error_string
            sys.exit(1)
        try:
            info = simplejson.loads(self.client._get_resource( 
                                    url,
                                    parameters = parameters,
                                    token=access_token ))
        except:
            return []
        else:
            return info

    def get_ratings(self, disc_info=[], urls=[]):
        access_token=self.access_token

        if not isinstance(access_token, oauth.OAuthToken):
            access_token = oauth.OAuthToken( 
                                    access_token['key'], 
                                    access_token['secret'] )

        request_url = '/users/%s/ratings/title' % (access_token.key)
        if not urls:
            if isinstance(disc_info,list):
                for disc in disc_info:
                    urls.append(disc['id'])
            else:
                urls.append(disc_info['id'])
        parameters = { 'title_refs': ','.join(urls), 'output': 'json' }

        info = simplejson.loads( self.client._get_resource( 
                                    request_url, 
                                    parameters=parameters, 
                                    token=access_token ) )

        ret = {}
        for title in info['ratings']['ratings_item']:
                ratings = {
                        'average': title['average_rating'],
                        'predicted': title['predicted_rating'],
                }
                try:
                    ratings['user'] = title['user_rating']
                except:
                    pass

                ret[ title['title']['regular'] ] = ratings

        return ret

    def get_rental_history(self,history_type=None,start_index=None,
                                    max_results=None,updated_min=None):
        access_token=self.access_token
        parameters = {}
        if start_index:
            parameters['start_index'] = start_index
        if max_results:
            parameters['max_results'] = max_results
        if updated_min:
            parameters['updated_min'] = updated_min

        if not isinstance(access_token, oauth.OAuthToken):
            access_token = oauth.OAuthToken( 
                                    access_token['key'],
                                    access_token['secret'] )

        if not history_type:
            request_url = '/users/%s/rental_history' % (access_token.key)
        else:
            request_url = '/users/%s/rental_history/%s' % (access_token.key,history_type)

        try:
            info = simplejson.loads( self.client._get_resource( 
                                    request_url,
                                    parameters=parameters,
                                    token=access_token ) )
        except:
            return {}

        return info


class NetflixUserQueue:

    def __init__(self,user):
        self.user = user
        self.client = user.client
        self.tag = None

    def get_contents(self, sort=None, start_index=None, 
                                    max_results=None, updated_min=None):
        parameters={'output': 'json'}
        if start_index:
            parameters['start_index'] = start_index
        if max_results:
            parameters['max_results'] = max_results
        if updated_min:
            parameters['updated_min'] = updated_min
        if sort and sort in ('queue_sequence','date_added','alphabetical'):
            parameters['sort'] = sort

        request_url = '/users/%s/queues' % (self.user.access_token.key)
        try:
            info = simplejson.loads(self.client._get_resource( 
                                    request_url,
                                    parameters=parameters,
                                    token=self.user.access_token ))
        except:
            return []
        else:
            return info

    def get_available(self, sort=None, start_index=None, 
                                    max_results=None, updated_min=None,
                                    queue_type='disc'):
        parameters={'output': 'json'}
        if start_index:
            parameters['start_index'] = start_index
        if max_results:
            parameters['max_results'] = max_results
        if updated_min:
            parameters['updated_min'] = updated_min
        if sort and sort in ('queue_sequence','date_added','alphabetical'):
            parameters['sort'] = sort

        request_url = '/users/%s/queues/%s/available' % (
                                    self.user.access_token.key,
                                    queue_type)
        try:
            info = simplejson.loads(self.client._get_resource( 
                                    request_url,
                                    parameters=parameters,
                                    token=self.user.access_token ))
        except:
            return []
        else:
            return info

    def get_saved(self, sort=None, start_index=None, 
                                    max_results=None, updated_min=None,
                                    queue_type='disc'):
        parameters={'output': 'json'}
        if start_index:
            parameters['start_index'] = start_index
        if max_results:
            parameters['max_results'] = max_results
        if updated_min:
            parameters['updated_min'] = updated_min
        if sort and sort in ('queue_sequence','date_added','alphabetical'):
            parameters['sort'] = sort

        request_url = '/users/%s/queues/%s/saved' % (
                                    self.user.access_token.key,
                                    queue_type)
        try:
            info = simplejson.loads(self.client._get_resource( 
                                    request_url,
                                    parameters=parameters,
                                    token=self.user.access_token ))
        except:
            return []
        else:
            return info

    def add_title(self, disc_info=[], urls=[],queue_type='disc',position=None):
        access_token=self.user.access_token
        parameters={}
        if position:
            parameters['position'] = position

        if not isinstance(access_token, oauth.OAuthToken):
            access_token = oauth.OAuthToken( 
                                    accessToken['key'],
                                    accessToken['secret'] )

        request_url = '/users/%s/queues/disc' % (access_token.key)
        if not urls:
            for disc in disc_info:
                urls.append( disc['id'] )
        parameters['title_ref'] = ','.join(urls)

        if not self.tag:
            params = {'output': 'json'}
            response = self.client._get_resource(
                                    request_url,
                                    parameters = params,
                                    token=access_token )
            response = simplejson.loads(response)
            self.tag = response["queue"]["etag"]
        parameters['etag'] = self.tag
        response = self.client._post_resource( 
                                    request_url, 
                                    token=access_token,
                                    parameters=parameters )
        return response

    def remove_title(self, id, queue_type='disc'):
        access_token=self.user.access_token
        entry_iD = None
        parameters={'output': 'json'}
        if not isinstance(access_token, oauth.OAuthToken):
            access_token = oauth.OAuthToken(
                                    access_token['key'],
                                    access_token['secret'] )

        # First, we gotta find the entry to delete
        queueparams = {'max_results': 500, 'output': 'json'}
        request_url = '/users/%s/queues/disc' % (access_token.key)
        response = self.client._get_resource( 
                                    request_url,
                                    token=access_token,
                                    parameters=queueparams )
        print "Response is " + response
        response = simplejson.loads(response)
        titles = response["queue"]["queue_item"]

        for disc in titles:
            disc_iD = os.path.basename(urlparse(disc['id']).path)
            if disc_iD == id:
                entry_iD = disc['id']

        if not entry_iD:
            return
        first_response = self.client._get_resource( 
                                    entry_iD,
                                    token=access_token,
                                    parameters=parameters )

        response = self.client._delete_resource( entry_iD, token=access_token )
        return response

class _NetflixAPI(object):
    """ Abstract Class for the common api of Netflix V1.0 and V2.0"""

    _user_credential_set = False
    _api_version = 2.0

    def __init__(self, appname, consumer_key, consumer_secret, access_token=None,
            access_token_secret=None, logger=None):
        """ **Abstract class** contains all the common functionality of netflix v1 and v2 REST api

        :param appname: The Application name as registered in Netflix Developer 
            website <http://developer.netflix.com/apps/mykeys>
        :param consumer_key: The consumer key as registered in Netlflix Developer website
        :param consumer_secret: The consumer secret as registerde in Netflix Developer website
        :param access_token: (Optional) User access token obtained using OAuth three legged authentication 
        :param access_token_secret: (Optional) User access token  secret obtained using OAuth 
            three legged authentication 
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

        self._user_credential_set = False
        if access_token and access_token_secret:
            self.set_user_credential(access_token, access_token_secret)
        else:
            oauth_hook = OAuthHook()
            self._client = requests.session(hooks={'pre_request': oauth_hook})


    def set_user_credential(self, access_token, access_token_secret):
        """ Sets the user access token and secret for future calls
        Must be set for calls that require a user to be authenticated"""

        if not access_token:
            raise NetflixError("access_token cannot be null/empty")
        if not access_token_secret:
            raise NetflixError("access_token_secret cannot be null/empty")

        oauth_hook = OAuthHook(access_token, access_token_secret)
        self._client = requests.session(hooks={'pre_request': oauth_hook})
        self._user_credential_set = True
        self._access_token = access_token

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
        return (OAuthToken(request_token, request_secret), auth_url )

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


    def get_user(self, id=None):
        """ Retrieves subscriber infomation

        :param id: Retrieves information about the user whose ``id`` is given. If ``id`` is not given
            the current user's infomation is retrieved

        :returns: ``dict`` object containg user information. The return object is different for `v1` and `v2`
        """

        self._assert_authorized()
        if not id:
            id = self._access_token
        url_path = '/users/' + id
        return self._request('get', url_path).json

    def get_user_details(self, subtype, id=None):
        self._assert_authorized()
        url_path = '/users/' + self._access_token + "/" + subtype
        return self._request('get', url_path).json

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

    def _request(self, method, url, data={}, headers={}):
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
        r = self._client.request(method, url, data=data, config=config, headers=headers)
        self._log((r.request.method, r.url, r.status_code))
        if(r.status_code < 200 or r.status_code >= 300):
            raise NetflixError("Error fetching url: {0}. Code: {1}. Error: {2} "
                    .format(r.url, r.status_code, r.content))
        return r

    def __str__(self):
        return self.attributes()  


class NetflixAPIV1(_NetflixAPI):
    """ Provides functional interface to Netflix V1 REST api"""

    def __init__(self, appname, consumer_key, consumer_secret, access_token=None,
            access_token_secret=None, logger=None):
        """ The main class for accessing the Netflix REST API v1.0 http://developer.netflix.com/docs/REST_API_Reference
        It provides all the methods needed to access the resources exposed by netflix. Netflix has now released version 2.0
        http://developer.netflix.com/page/Netflix_API_20_Release_Notes which is backward incompatible. So going forward netflix
        may *deprectate* the version 1.0 APIs. So it is recommended to use version 2.0 API instead 

        :param appname: The Application name as registered in Netflix Developer 
            website <http://developer.netflix.com/apps/mykeys>
        :param consumer_key: The consumer key as registered in Netlflix Developer website
        :param consumer_secret: The consumer secret as registered in Netflix Developer website
        :param access_token: (Optional) User access token obtained using OAuth three legged authentication 
        :param access_token_secret: (Optional) User access token  secret obtained using OAuth 
            three legged authentication 
        :param logger: (Optional) The stream object to write log to. Nothing is logged if `logger` is `None`
        """
        super(NetflixAPIV1, self).__init__(appname, consumer_key, consumer_secret, access_token,
            access_token_secret, logger)
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

    def __init__(self, appname, consumer_key, consumer_secret, access_token=None,
            access_token_secret=None, logger=None):
        """ The main class for accessing the Netflix REST API v2.0 http://developer.netflix.com/page/Netflix_API_20_Release_Notes
        It provides all the methods needed to access the resources exposed by netflix. The version 2.0 of the API 
        is backward incompitable. So going forward netflix may *deprectate* the version 1.0 APIs. So it is 
        recommended to use this class for accessing netflix API.

        :param appname: The Application name as registered in Netflix Developer 
            website <http://developer.netflix.com/apps/mykeys>
        :param consumer_key: The consumer key as registered in Netlflix Developer website
        :param consumer_secret: The consumer secret as registerde in Netflix Developer website
        :param access_token: (Optional) User access token obtained using OAuth three legged authentication 
        :param access_token_secret: (Optional) User access token  secret obtained using OAuth 
            three legged authentication 
        :param logger: (Optional) The stream object to write log to. Nothing is logged if `logger` is `None`
        """
        super(NetflixAPIV2, self).__init__(appname, consumer_key, consumer_secret, access_token,
            access_token_secret, logger)
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



