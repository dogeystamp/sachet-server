Server CLI
==========

The Sachet server has a basic CLI interface for management.

It can be accessed via the following command::

    flask --debug --app sachet.server

.. note::
    
    The ``--debug`` flag tells Sachet we are in development mode.
    In production, remove it.

Any command or subcommand has information on how to use it via ``<cmd> --help``.

User
----

To create a user::

    flask --debug --app sachet.server user create --username jeff --password password123

To create an administrator user::

    flask --debug --app sachet.server user create --username admin --admin yes --password password123

.. warning::

   Setting the password via the command-line is not safe.
   In a real environment, you should reset this password immediately (see :ref:`authentication_password_change`.)

To delete a user::
    
    flask --debug --app sachet.server user delete jeff

Database
--------

The database is managed via Flask-Migrate.
See their `documentation <https://flask-migrate.readthedocs.io/en/latest/>`_ for more information.
