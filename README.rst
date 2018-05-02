ENSEK
=======

|PyPI| |Python Versions| |Build Status|

🐍 Python Client for the ENSEK API (http://www.ensek.co.uk/)
This client does not implement all the features of the API, pull requests are very welcome to expand functionality.

Installation
------------

To install ensek, simply:

.. code:: bash

    pip install ensek

How To Use
----------

Initialise the client
~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    from ensek import Ensek
    client = Ensek(
        api_url='https://api.usio.ignition.ensek.co.uk/',
        api_key='fill_this_in',
    )

Available methods
~~~~~~~~~~~~~~~~~

**Get an account by id**

``client.get_account(account_id=123)``

**Get tariffs for an account by id**

``client.get_account_tariffs(account_id=123)``

**Get meter points for an account by id**

``client.get_meter_points(account_id=123)``

**Get recent newly registered accounts**

``client.get_completed_signups()``

**Get the account id currently associated with an MPAN core id**

``client.get_account_for_meter_point(mpan_core_id='9910000001507')``

**Get the PES Area for a postcode** (`<http://www.energybrokers.co.uk/electricity/PES-Distributor-areas.htm>`_)

``client.get_region_id_for_postcode(postcode='se14yu')``

**Get gas utility information for a MPRN (meter point reference number)**

``client.get_gas_utility(mprn='3226987202')``

Note: For each client method:

- If API response is 404, method will raise ``LookupError``.
- If API response is between 400 and 499, method will raise ``ValueError``.
- For any other bad status code ``EnsekError`` will raise.


Requirements
------------

::

    1. Python 3.6+
    2. See requirements.txt

Running the tests
-----------------

.. code:: bash

    pip install -r requirements-test.txt
    pytest

Releasing to PyPI
-----------------

.. code:: bash

    pip install zest.releaser
    fullrelease
    
.. |PyPI| image:: https://img.shields.io/pypi/v/ensek.svg
   :target: https://pypi.python.org/pypi/ensek
.. |Python Versions| image:: https://img.shields.io/pypi/pyversions/ensek.svg
   :target: https://pypi.python.org/pypi/ensek
.. |Build Status| image:: https://travis-ci.org/Usio-Energy/ENSEK.png?branch=master
   :target: https://travis-ci.org/Usio-Energy/ensek
