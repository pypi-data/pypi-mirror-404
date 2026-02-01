Changelog
=========


[0.2.10] - December 3 2025
--------------------------

- Error logging improved for timeseries database writes.
- Dependencies to the recent masterpiece releases updated
  

[0.2.9] - December 1 2025
-------------------------
- 'spothintafi.py' removed and implemented as separate 'juham-spothintafi' plugin


[0.2.8] - December 1 2025
-------------------------
- LeakDetector migrated from juham-watermeter
- Obsolete debug logging removed from the LeakDetector


[0.2.6] - November 30 2025
--------------------------

- More agressive spot sensitivity.

  

[0.2.5] - 2025-11-21
--------------------

- Project development status elevated to **Beta**.
- Added an electricity-forecast–aware heating algorithm:
  If today's electricity price is high and tomorrow's is lower, the system
  automatically reduces heating today to optimize cost.
- Introduced **SupervisorThread**, responsible for:
  - Detecting and listing crashed threads
  - Logging failures
  - Automatically restarting affected threads
- Added a significant number of new unit tests to improve stability and
  coverage.
- Extracted **powermeter_simulator.py** into a separate simulation plugin
  for cleaner architecture and modularity.

  

[0.1.13] - Nov 15, 2025
-----------------------

- Installation instructions added into README.rst
- Failure in **ts/log_ts.py** logging method logged the failure, leading to Infinite logging loop. Fixed.


[0.1.11] - Nov 11, 2025
-----------------------

- New heating plan attributes published to timeseries
- Heating plan now includes flags indicating whether temperature and solar power forecasts were used.
- Min and max temperature limits published with the powerplan.
- Minor issues in docstrings fixed.
- Unit tests updated to reflect new heating plan attributes.


[0.1.5] - Nov 07, 2025
----------------------

- Heating plan optimization logic improved to better account for temperature and solar power forecasts.
- Unit tests added for significantly higher coverage.
- Documentation updated to reflect changes in temperature and solar power forecast handling.
- SolarForecast and TemperatureForecast fields added to PowerPlan time series.



[0.1.3] - Nov 01, 2025
----------------------

- Added support for arbitrary energy balancing intervals in the automation module. 
- Default energy balancing interval changed from 1 hour to 15 minutes to comply with the new EU energy market directive.
- Updated energy cost calculator and heating optimizer components to work with configurable intervals.
- Improved unit tests to validate behavior across various interval lengths.



[0.1.1] - Oct 28, 2025
----------------------

- Project status elevated from Pre-Alpha to Alpha.
- The default energy balancing interval for **HeatingOptimizer** is now 15 minutes.
- Added "converage" package to [project.optional-dependencies] in pyproject.toml



[0.0.73] - Aug 30, 2025
-----------------------

- Default boiler temperature limits adjusted.


[0.0.34] - May 02, 2025
-----------------------

- Weight attribute added to heatingoptimizer. Determines how large a share of the time slot 
  a consumer receives compared to others.
 

  
[0.0.33] - May 01, 2025
-----------------------

- Workaround to Sphinx issue with multiply defined instance variables.


[0.0.32] - April 27, 2025
-------------------------

* **HeatingOptimizer** single minimum and maximum temperature attributes replaced by a montly limits.
  
.. code-block:: python

    pip install masterpiece_plugin
    boiler.temperature_limits = {
        1: (50, 68),  # January: colder, need hotter heating water
        2: (50, 68),  # February
        3: (50, 68),  # March
        4: (40, 68),  # April
        5: (30, 68),  # May
        6: (30, 68),  # June: warmer, need less heating
        7: (30, 68),  # July
        8: (30, 68),  # August
        9: (40, 68),  # September
        10: (50, 68),  # October
        11: (50, 68),  # November
        12: (50, 68),  # December
    }

* **HeatingOptimizer** class attributes documented.



[0.0.31] - April 21, 2025
-------------------------

* EnergyBalancer and EnergyBalancerTs classes improved. There is now two MQTT sub-topics: status,
  for controlling consumers, and diagnostics for monitoring the operation of the energy balancer.


[0.0.29] - April 20, 2025
-------------------------

* Bug fixes to EnergyBalancer.
* PriceForecast class updated (not there yet)

[0.0.28] - April 20, 2025
-------------------------

* EnergyBalancer logic improved. Instead of activating all consumers at the same time, it now activates them one at a time
  in a serialized manner to minimize the maximum power (and fuse capacity, which affects the energy bill) required
  during balancing cycles. 


[0.0.27] - April 16, 2025
-------------------------

* CI pipeline unification.
* EnergyBalacing features isolated from the HeatingOptimizer and implemented as a separate energybalancer module.



[0.0.23] - April 04, 2025
-------------------------
* The HotWaterOptimizer class has been renamed to HeatingOptimizer to better reflect its general-purpose nature.
* Added test_energybalancer.py
* Added publish_diagnostics() method to track energy balance driven heating.
* Added heatingoptimizer_ts module to support time series recording.
* Fixed bug in net-energy balancing system.
* Removed redundand dependencies in ``pyproject.toml``.
* Enabled net energy balance feature.
  

[0.1.12] - March 03, 2025
-------------------------

* Updated for the new modularized ci-templates and docs
* New unit tests written, for better coverage. Not nearly there yet.


[0.1.8-10] - February 23, 2025
------------------------------

* Support for grid (network) prices and tax added.

* Bug fix in the computation of the utilization optimization index: solar power was previously
  given in kW, while radiator power was in W, which underestimated the effect of available solar power.

* New attribute added to time series: GridCost (cost and tax per kWh)
  


[0.1.7] - February 08, 2025
---------------------------

Initial release for GitLab. Pre-alpha!

