=============
dq db manager
=============


.. image:: https://img.shields.io/pypi/v/dq_db_manager.svg
        :target: https://pypi.python.org/pypi/dq_db_manager

.. image:: https://img.shields.io/travis/Data-Quotient/dq_db_manager.svg
        :target: https://travis-ci.com/Data-Quotient/dq_db_manager

.. image:: https://readthedocs.org/projects/dq-db-manager/badge/?version=latest
        :target: https://dq-db-manager.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status




Database management library for the DQ platform


* Free software: Apache Software License 2.0
* Documentation: https://dq-db-manager.readthedocs.io.


Features
--------

* Unified interface for multiple database backends
* PostgreSQL, MySQL/MariaDB, Oracle, Vertica, CockroachDB, and SQLite support
* Amazon S3 data source integration
* Automatic metadata extraction (tables, columns, constraints, indexes, views, triggers)
* Pydantic-based metadata models

Installation
------------

Install the core package::

    pip install dq_db_manager

Install with database-specific extras::

    pip install "dq_db_manager[postgresql]"
    pip install "dq_db_manager[oracle]"
    pip install "dq_db_manager[mariadb]"
    pip install "dq_db_manager[vertica]"
    pip install "dq_db_manager[s3]"
    pip install "dq_db_manager[all]"

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
