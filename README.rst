pyflix2: python module for accessing Netflix webservice
=======================================================

Introduction
------------

*pyflix2* is a `BSD licensed` python module for accessing netflix API (both v1 and v2)
Netflix provides REST interfaces to access it's catalog and various user data.
This module exposes easy to use object oriented interfaces that is inteded to make it even easier
for python programmers to use.

Install
-------
Installing requests is simple with `pip <http://www.pip-installer.org/>`_::

    $ pip install pyflix2

or, with `easy_install <http://pypi.python.org/pypi/setuptools>`_::

    $ easy_install pyflix2


Example
-------

::

    from pyflix2 import *

    netflix = NetflixAPIV2( 'appname', 'key', 'shared_secret')
    movies = netflix.title_autocomplete('Terminator', filter='instant')
    for title in movies['autocomplete']['title']:
        print title

    user = netflix.get_user('access_token', 'access_token_secret')
    reco = user.get_reccomendations()
    for movie in reco['recommendations']:
        print movie['title']['regular']

Note
    - Here ``appname``, ``key`` and ``shared_secret`` needs to be obtained from: http://developer.netflix.com/apps/mykeys.
    - The ``access_token``, ``access_token_secret`` needs to be obtained programmatically using ``get_request_token``
      and ``get_access_token``


Commandline
-----------
::

    $ python -mpyflix2 -s 'the matrix' -x 

Or see help::

    $ python -mpyflix2 -h


Features
--------

- Supports both V1 and V2 of netflix REST API
- Supports both out-of-bound (oauth 1.0a) and  vanila three legged oauth auhentication
- Provides easy to use and well documented functional interface for all the API exposed by netflix
- Throws Exception for all kinds of error situation making it easier to integrate with other program
- V1 and V2 APIs are exposed using different classes, so version specific features can be used easily
- Internally uses `Requests <https://github.com/kennethreitz/requests>`_ for making HTTP calls
- Want any new feature? please `file a feature request <https://github.com/amalakar/pyflix2/issues/new>`_

Documentation: http://pyflix2.readthedocs.org/en/latest/index.html

Note: I would like to thank Kirsten Jones for the library http://code.google.com/p/pyflix/
As pyflix2 was initially inspired by pyflix.

.. _`the repository`: https://github.com/amalakar/pyflix2
