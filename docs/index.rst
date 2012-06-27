
.. include:: ../README.rst

User Guide
----------

.. default-domain:: py

All of pyflix2's functionality can be access via the classes  :py:class:`~Netflix.NetflixAPIV1` or :py:class:`~Netflix.NetflixAPIV2` based on
the version you want to use and :py:class:`~Netflix.User`.

.. currentmodule:: Netflix

Netflix API endpoint to Method Mapping
--------------------------------------

.. include:: api_table.rst

API
---

.. autoclass:: Netflix.NetflixAPIV2
   :inherited-members:
   :members:
   :undoc-members:

   .. automethod:: __init__


---------------------

.. autoclass:: Netflix.NetflixAPIV1
   :inherited-members:
   :members:
   :undoc-members:

   .. automethod:: __init__

---------------------

.. autoclass:: Netflix.User
   :inherited-members:
   :members:
   :undoc-members:

   .. automethod:: __init__


---------------------

.. autoexception:: Netflix.NetflixError
