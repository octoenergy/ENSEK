.. :changelog:

Release History
---------------

1.7.0 (2018-09-26)
++++++++++++++++++

- Adds ``update_account_attribute`` method.
- Adds ``get_account_attributes`` method.

1.6.0 (2018-09-12)
++++++++++++++++++

- Adds ``get_account_settings`` method.


1.5.0 (2018-09-12)
++++++++++++++++++

- Adds ``get_addresses_at_postcode`` method.


1.4.1 (2018-08-10)
++++++++++++++++++

- Bugfix ``get_all_account_ids`` method, was previously returning a subset of the total ids.


1.4.0 (2018-08-10)
++++++++++++++++++

- Adds ``get_live_balances`` method.
- Adds ``get_live_balances_detailed`` method.


1.3.0 (2018-07-30)
++++++++++++++++++

- Adds optional ``source`` arg to ``create_meter_reading`` method.


1.2.0 (2018-07-24)
++++++++++++++++++

- Adds ``get_meter_point_readings`` method.
- Adds ``create_meter_reading`` method.


1.1.0 (2018-07-11)
++++++++++++++++++

- Adds ``get_electricity_utility`` method.


1.0.0 (2018-07-09)
++++++++++++++++++

- Renames parameter of ``get_account_for_meter_point`` to ``meter_point_id``.


0.3.0 (2018-04-27)
++++++++++++++++++

- Adds ``get_gas_utility`` method.


0.2.1 (2018-04-19)
++++++++++++++++++

- Bugfix for ``EnsekError`` not being raised when a connection error occurs.


0.2.0 (2018-04-19)
++++++++++++++++++

- Adds ``get_region_id_for_postcode`` method.


0.1.0 (2018-04-18)
++++++++++++++++++

- Initial release
