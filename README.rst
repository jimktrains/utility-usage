Utility Usage Collator
----------------------

Downloads usage and billing information from utility providers. Until the
providers get with the times and offer a sensible API and credential
delegation, we're just going to have to screen-scrape.

For now, sqlite is perfectly adequate for this task.

Support for:

amwater
    American Water Works Company, Inc. (and subsidiaries such as Pennsylvania American Water)

duqlight
  Duqueusne Light Company

colgaspa
  Columbia Gas of Pennsylvania

Config
=======
The `config.ini` needs to be set up correctly to gather information from the
utilities. Currently, that means:

.. code-block::

    [storage]
    download_path=

    [amwater]
    username=
    password=
    
    [duqlight]
    username=
    password=

ToDo
=====

So, I'd like to move SQLAlchemy for the db interactions.

I'd also like to clean up where the config is loaded from.
