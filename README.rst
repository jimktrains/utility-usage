Utility Usage Collator
----------------------

Downloads usage and billing informate from utility providers. Until the
providers get with the times and offer a sensible API and credential
deligation, we're just going to have to screen-scrape.

For now, sqlite is perfectly adequate for this task.

Support for:

amwater
    American Water Works Company, Inc. (and subsidaries such as Pennsalvania American Water)

duqlight
  Duqueusne Light Company

## Config
The `config.ini` needs to be set up correctly to gather information from the
utilities. Currently, that means:

.. code-block::

    [amwater]
    username=
    password=
    
    [duqlight]
    username=
    password=
