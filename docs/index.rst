.. Sachet documentation master file, created by
   sphinx-quickstart on Wed May 17 20:46:47 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Sachet's documentation!
==================================

Sachet is a small file-sharing server.

development
-----------

To start sachet in dev mode:

Clone the repo::

    git clone https://github.com/dogeystamp/sachet
    cd sachet

Create a venv with required dependencies::

    python -m venv venv
    source venv/bin/activate
    python -m pip3 install -r requirements.txt

Create a configuration file (and set the secret key!)::

    cp config.yml.example config.yml
    vim config.yml

Start Flask in development mode::

    flask --debug --app sachet.server run

tests
^^^^^

Run tests with pytest::

    pytest --cov --cov-report term-missing

linting
^^^^^^^

Please use the linter before submitting code::

    black .

database maintenance
--------------------

To clean up the database (remove stale entries)::

    flask --app sachet.server cleanup

Otherwise, to upgrade the database after a schema change::

    flask --app sachet.server db upgrade

.. toctree::
   :maxdepth: 2
   :caption: Contents:



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
