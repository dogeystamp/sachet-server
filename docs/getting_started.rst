Getting started
===============

.. note::

    Currently, Sachet does not have the configs to run under WSGI for production yet.
    This page only explains how to get Sachet up and running for development purposes.

Installation
------------
Clone the repo::

    git clone https://github.com/dogeystamp/sachet-server
    cd sachet-server

Create a venv with required dependencies::

    python -m venv venv
    source venv/bin/activate
    python -m pip install -r requirements.txt

Create a configuration file::

    cp config.yml.example config.yml

Remember to set up a secret key in ``config.yml``:

.. code-block:: yaml

   SECRET_KEY: "41DJjqp6+Ztk9krJkwbZem1+JijowDU6ifkgdntF2FK3ygi5HM"

.. note::

   You can generate a secret key using the following command on Linux::

       cat /dev/urandom | base64 | head -c 50

.. warning::

   Keep this secret key safe!
   If you leak this key, a malicious attacker could authenticate as any user on your server.

Initialize the database::

    flask --debug --app sachet.server db upgrade

Set up an administrator user::

    flask --debug --app sachet.server user create --username admin --admin yes --password password123

.. warning::

   Setting the password via the command-line is not safe.
   In a real environment, you should reset this password immediately (see :ref:`authentication_password_change`.)

You can now start Sachet in development mode::
    
    flask --debug --app sachet.server run

Development
-----------

.. note::
    
    This section also requires being in the virtual environment::

        source venv/bin/activate

Testing
^^^^^^^

You can run tests using pytest::

    pytest --cov --cov-report term-missing

Linting
^^^^^^^

Please use the linter before submitting code::

    black .

Database maintenance
--------------------

To clean up the database (remove stale entries)::

    flask --app sachet.server cleanup

Otherwise, to upgrade the database after a schema change::

    flask --app sachet.server db upgrade

Documentation
-------------

This documentation is built using Sphinx with the following steps.

First, create a new virtual environment for documentation-related dependencies::

    python -m venv .docvenv
    source .docvenv/bin/activate
    python -m pip install -r docs/requirements.txt

Then, build docs::

    make -C docs html

You can now view the documentation with a web browser::

    xdg-open docs/_build/html/index.html
