pyflix2: python module for accessing Netflix webservice
=======================================================
Release v\ |version|.

pyflix2 is a `BSD licensed` python module for accessing netflix API (both v1 and v2)

.. code-block:: python

    netflix = NetflixAPIV2( 'appname', 'key', 'shared_secret')
    movies = netflix.title_autocomplete('Terminator', filter='instant')
    for title in movies['autocomplete']['title']:
        print title


.. code-block:: python

    user = netflix.get_user('access_token', 'access_token_secret')
    reco = user.get_reccomendations()
    for movie in reco['recommendations']:
        print movie['title']['regular']

Note: 

- Here ``appname``, ``key`` and ``shared_secret`` needs to be obtained from: http://developer.netflix.com/apps/mykeys.
- The ``access_token``, ``access_token_secret`` needs to be obtained programmatically using :py:meth:`~NetflixAPIV2.get_request_token` 
  and :py:meth:`~NetflixAPI.get_access_token`

Features
--------

- Supports both V1 and V2 of netflix REST API
- Supports both out-of-bound (oauth 1.0a) and  vanila three legged oauth auhentication
- Provides easy to use and well documented functional interface for all the API exposed by netflix
- Throws Exception for all kinds of error situation making it easier to integrate with other program
- V1 and V2 APIs are exposed using different classes, so version specific features can be used easily
- Internally uses `Requests <https://github.com/kennethreitz/requests>`_ for making HTTP calls
- Want any new feature? please `file an issue <https://github.com/amalakar/pyflix2/issues/new>`_

Documentation: http://pyflix2.readthedocs.org/en/latest/index.html

.. _`the repository`: https://github.com/amalakar/pyflix2
