A python wrapper around the netflix API
=======================================


In order to use the system, you need to get a developer key/secret from the Netflix developer site.  You will need those for all requests to Netflix.

To help you get a better understanding of how this works, here's a step by step tutorial.

- Get a developer API key and secret
- Put those values in the example.py script
- Run the example.py script.  In this configuration it will perform all of the actions it can do without an authenticated user.
- Run the example.py script with the "-a" flag.  Since you don't already have user keys, it will start the process of retrieving them.
- Visit the website listed, and insert the request values into the example.py script under EXAMPLE_USER['request']
- Run the example.py script again with the "-a" flag.  This will generate the access values.  Insert those into the script under EXAMPLE_USER['access']
- At this point you can do any of the actions with example.py -a

In your own coding you may want to run these steps differently, or more silently.  You can retain the configuration within your application.  The example is somewhat clunky but should help you understand what can be done with the various levels of authentication.

Note: This code was originally based on Pyflix <http://code.google.com/p/pyflix/> but it has been refactored and changed heavily.
And very little trace of original code can be found. But when I started I based it on pyflix 
Features
--------

- Supports both V1 and V2 of netflix REST API
- Supports both out-of-bound (oauth 1.0a) and  vanila three legged oauth auhentication (oauth)
- Internally uses Requests <https://github.com/kennethreitz/requests> for making HTTP calls


.. _`the repository`: https://github.com/amalakar/pyflix2
