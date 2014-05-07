.. :changelog:

History
-------
0.2.1 (2014-04-29)
++++++++++++++++++
- Adding a new method to download the entire catalog into a file.

0.2.0 (2013-01-26)
++++++++++++++++++
- Issue #6: Add support for downloading full catalog in lib as well as in command line 
- Issue #8: Incorporate netflix api change to api-public.netflix.com
- Issue #9: Update codebase to work with requests v1.1.0

Backward incompatible changes
-----------------------------
- ``get_user`` api signature has changed (require one more parameter ``user_id``)
- Addition of ``user_id`` in ``~/.pyflix.cfg``
- ``get_access_token`` returns additional ``user_id``

0.1.3 (2012-07-09)
++++++++++++++++++
- Fixed access token retrival code in __main__.py
- Fixed typo in sample config file

0.1.2 (2012-07-06)
+++++++++++++++++++
- Issue #5: Fixed circular dependency in setup.py

0.1.1 (2012-07-04)
+++++++++++++++++++

- Initial version
