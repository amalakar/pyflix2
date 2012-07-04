
.. include:: ../README.rst

User Guide
----------

.. default-domain:: py

All of pyflix2's functionality can be access via the classes  :py:class:`~pyflix2.NetflixAPIV1` or :py:class:`~pyflix2.NetflixAPIV2` based on
the version you want to use and :py:class:`~pyflix2.User`.

.. currentmodule:: pyflix2

Netflix API endpoint to Method Mapping
--------------------------------------

.. include:: api_table.rst

API
---
.. autodata:: pyflix2.EXPANDS
.. autodata:: pyflix2.SORT_ORDER
.. autodata:: pyflix2.RENTAL_HISTORY_TYPE

.. autoclass:: pyflix2.NetflixAPIV2
   :inherited-members:
   :members:
   :undoc-members:

   .. automethod:: __init__


---------------------

.. autoclass:: pyflix2.NetflixAPIV1
   :inherited-members:
   :members:
   :undoc-members:

   .. automethod:: __init__

---------------------

.. autoclass:: pyflix2.User
   :inherited-members:
   :members:
   :undoc-members:

   .. automethod:: __init__


---------------------

.. autoexception:: pyflix2.NetflixError
