Changelog for Automation
==========================

New in v1.7.0 (2024-02-26)
------------------------------

New features:

* Convert ``pyodbc`` references to ``sqlalchemy``

New in v1.6.2 (2024-01-12)
------------------------------

New features:

* Add new ``write_file`` parameter to ``misc.initiate_logging`` to bypass file write

New in v1.6.1 (2023-12-26)
------------------------------

Bugfixes:

* Allow ``script_name`` to actually matter in ``misc.initiate_logging``, that's what
  I get for not actually testing

New in v1.6.0 (2023-12-26)
------------------------------

New features:

* Addition of new function ``misc.initiate_logging`` to perform standard set-up
* Addition of new function ``misc.list_to_html`` to convert a list to an HTML table,
  with an optional header indicated

New in v1.5.3 (2023-12-20)
------------------------------

Changes:

* Upgrade dependencies in ``setup.py`` from == to >=

New in v1.5.2 (2023-12-05)
------------------------------

Changes:

* Upgrade dependencies

New in v1.5.1 (2023-09-15)
------------------------------

Changes:

* Switch logging write to reference ``os.sep`` instead of ``os.pathsep`` in ``sftp``
  and ``ftp``

Bugfixes:

* Fix path separator issues in ``office.excel``
* Calculate queries that are refreshing asyncronously in ``office.excel``


New in v1.5.0 (2023-08-26)
------------------------------

New features:

* New module ``ftp`` for standard FTP connections

Changes:

* Refactor ``db.db.script_objects`` to use ``subprocess.run`` instead of ``os.system``

Bugfixes:

* Add loop to keep trying to delete original directory in ``db.db.script_objects``
  since ``shutil`` does not always release its lock immediately


New in v1.4.1 (2023-08-22)
------------------------------

Changes:

* Strip out < and > characters from the exception_type value being included in
  ``misc.log_exception``


New in v1.4.0 (2023-08-19)
------------------------------

New features:

* Add new parameter ``suppress_override`` to ``sftp.sftp.upload`` and ``sftp.sftp.download``
  to allow customizable override wildcards
* Logging entry in the event a file or wildcard is passed in ``local_files`` but
  cannot be uploaded
* Logging entry in the event a file or wildcard is passed in ``remote_files`` but
  cannot be downloaded

Changes:

* Make the name of the environment variable for the master password be a value
  in the config file

Bugfixes:

* Add error logging entry if an upload results in an exception and only include
  successful files in the return list
* Add error logging entry if an download results in an exception and only include
  successful files in the return list


New in v1.3.1 (2023-08-13)
------------------------------

Changes:

* Change log file naming convention in ``sftp.sftp`` from ``sftp_yyyymmddHHMMSS.log``
  to ``sftp_yyyymmddHHMMSS_HostName.log``


New in v1.3.0 (2023-08-12)
------------------------------

New features:

* Implement context manager for ``sftp.sftp``

Changes:

* Convert ``save_host_key`` variable in ``sftp.sftp._connectssh`` to class variable

Bugfixes:

* Adjust context manager in ``db.db`` to ensure proper variables are returned


New in v1.2.3 (2023-08-11)
------------------------------

New features:

* Allow ability to bypass SFTP host key verification in ``sftp.sftp``


New in v1.2.2 (2023-08-09)
------------------------------

Bugfixes:

* Retrieve host key information in function ``sftp._connectssh`` when writing for
  the first time


New in v1.2.1 (2023-08-08)
------------------------------

New features:

* Add function ``misc.log_exception`` for usage in logging uncaught exceptions


New in v1.2.0 (2023-08-07)
------------------------------

New features:

* Add support for YAML configuration files

Changes:

* Pivot to ``config_file`` full path references everywhere, rather than split path
  and filenames


New in v1.1.0 (2023-08-06)
------------------------------

New features:

* Add class function ``secrets.keepass.writecustomproperty`` to write custom property
  values to a Keepass entry
* New class ``secrets_constants`` for the validation lists of pgp and sftp Keepass
  entry custom properties

Changes:

* Rework class ``db.db`` to connect via connection string passed in class, rather
  than a config value. If no connection string is passed, will proceed without
  connecting to a DB
* Rework class function ``fileproc.manipulate.mergecsvfiles`` to use internal
  OS Copy command when ``header = False`` and be able to handle fixed-width files.
* Only use ``paramiko.AutoAddPolicy`` when determining host key information

New in v1.0.4 (2023-08-03)
------------------------------

New features:

* Create new class ``fileproc.manipulate`` with functions ``mergecsvfiles`` and
  ``wildcardcopy``

Changes:

* Convert archive directory name to a config variable ``archiveDirName``


New in v1.0.3 (2023-07-30)
------------------------------

Bugfixes:

* Revert attempt to dynamically construct ``install_requires`` in ``setup.py``
  since it did not work and I stupidly did not test it first


New in v1.0.2 (2023-07-30)
------------------------------

Changes:

* Rewrite method of determining if a file is encrypted or not in class ``automation.pgp``
  so it works for MS Office files


New in v1.0.1 (2023-07-29)
------------------------------

New features:

* Allow for a list of files to convert to be passed in ``automation.jsonstuff.reformat_json``
* Implement ability to extract columns by index using ``automation.office.convert.extract_columns``

Changes:

* Rename parameter ``file`` to ``files`` in ``automation.jsonstuff.reformat_json``
* Default config path is now defined as the environment variable **CONFIGPATH**
  if not provided
* Merge old ``constants.py`` with ``__init__.py``


New in v1.0.0 (2023-07-19)
-----------------------------

Initial rollout of project as a package.
