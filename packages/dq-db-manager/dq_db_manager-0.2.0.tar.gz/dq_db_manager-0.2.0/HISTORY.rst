=======
History
=======

0.2.0 (2026-01-31)
------------------

* Migrated from legacy ``setup.py`` to ``pyproject.toml`` as the single source of truth for package metadata.
* Added optional dependency extras for each database backend (``postgresql``, ``oracle``, ``mariadb``, ``mysql``, ``vertica``, ``s3``, ``cockroachdb``, ``all``).
* Added SQLite handler support.
* Bumped minimum Python version to 3.9.
* Fixed Python 3.9 compatibility for union type annotations.
* Declared ``pydantic>=2.0`` as a core dependency.

0.1.0 (2024-01-28)
------------------

* First release on PyPI.
