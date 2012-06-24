
.. include:: ../README.rst

User Guide
----------

All of pyflix2's functionality can be access via the classes  :py:class:`~Netflix.NetflixAPIV1` or :py:class:`~Netflix.NetflixAPIV2` based on
the version you want to use and :py:class:`~Netflix.User`.

==========================================================  =================================================================
API endpoint                                                        Method 
----------------------------------------------------------  -----------------------------------------------------------------

/catalog/titles                                             autofunction:: search_titles :py:meth:`~NetflixAPIV2.search_titles
/catalog/titles/autocomplete                                :py:meth:`~NetflixAPIV2.title_autocomplete
==========================================================  =================================================================

API
---

.. autosummary::
    .. toctree::

    ~Netflix.NetflixAPIV1
    ~Netflix.NetflixAPIV2

.. automodule:: Netflix
    :members:


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
