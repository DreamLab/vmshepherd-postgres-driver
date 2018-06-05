vmshepherd-runtime-postgres-driver
==================================


tests
-----

..
    make test

develop
-------

..
	make db
	make develop

run
---

Create config/settings.yaml file (the same as for vmshepherd) and insert the following section in a proper place:

::

    # ...

    runtime:
      driver: PostgresDriver
      host: (hostname -f)
      database: vmshepherd
      user: vmshepherd
      password: vmshepherd

    # ...

Next step run application

..
	make run

