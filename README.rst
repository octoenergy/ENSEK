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

**Get account live balances**

``client.get_live_balances(account_id=123)``

``client.get_live_balances_detailed(account_id=123)``

**Get tariffs for an account by id**

``client.get_account_tariffs(account_id=123)``

**Get meter points for an account by id**

``client.get_meter_points(account_id=123)``

**Get the account id currently associated with an MPAN core id or MPRN**

``client.get_account_for_meter_point(meter_point_id='9910000001507')``

**Get the PES Area for a postcode** (`<http://www.energybrokers.co.uk/electricity/PES-Distributor-areas.htm>`_)

``client.get_region_id_for_postcode(postcode='se14yu')``

**Get gas utility information for a MPRN (meter point reference number)**

``client.get_gas_utility(mprn='3226987202')``

**Get electricity utility information for a MPAN CORE ID (meter point administration number)**

``client.get_electricity_utility(mpan_core_id='3226987202')``

**Create a meter reading**

``client.create_meter_reading(account_id=1507, source='SMART', meter_point_id=1597, register_id=1496, value=2.0, timestamp=datetime(2018, 7, 24, 13, 49, 34, 661562, tzinfo=timezone.utc))``

**Get readings for a meter point**

``client.get_meter_point_readings(meter_point_id=1597)``

**Get all customer account ids**

``client.get_all_account_ids()``

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
