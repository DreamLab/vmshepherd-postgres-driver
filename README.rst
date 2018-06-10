vmshepherd-runtime-postgres-driver
==================================

Introduction
------------

Provides plugin for ``VmShepherd`` - driver allows to store runtime data and lock management in postgres database.


Installation
------------

Simply use ``pip``.

:: 

    pip install vmshepherd-runtime-postgres-driver

Library requires (as well as VmShepherd itself) python 3.6 or later.

Usage
-----

Install package (in the same environment as VmShepherd) and configure ``VmShepherd`` like:

::

    # ...

    runtime:
      driver: PostgresDriver
      host: (hostname -f)
      database: vmshepherd
      user: vmshepherd
      password: vmshepherd

    # ...


Available config options
------------------------

.. csv-table::
   :header: "Name", "Type", "Description", "Default value"
   :widths: 15, 10, 40, 10

   "host", "string", "Postgres DB host.", ""
   "port", "integer", "Postgres DB port.", "5432"
   "database", "string", "Postgres DB name.", ""
   "user", "string", "Postgres auth user.", ""
   "password", "string", "Postgres auth password.", ""
   "pool_size", "integer", "Postgres connection pool size.","2"



Develop
-------

Run tests:

::

    make test

Create local DB in docker and start vmshepherd:

::

	make db
	make develop


License
-------

`Apache License 2.0 <LICENSE>`_

