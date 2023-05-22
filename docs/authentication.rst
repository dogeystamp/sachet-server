Authentication
==============

Authentication is done via the ``Authorization`` HTTP header using a JSON Web Token (JWT).
As a client, there is no need to understand or parse JWTs; they can be considered as strings.

Signing in
----------
Signing in is done via ``POST /users/login``.

Use the following request body:
    
.. code-block:: json

    {
        "username": "your_username_here",
        "password": "your_password_here"
    }

The server will respond like this:

.. code-block:: json

    {
        "auth_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2ODUwNTgwNDcsImlhdCI6MTY4NDQ1MzI0Nywic3ViIjoidXNlciIsImp0aSI6bnVsbH0.nfJ06gLClROeS5rKg90pqaVikcr_-y00VbCTE3yK3fk",
        "message": "Logged in.",
        "status": "success",
        "username": "user"
    }

.. warning::

   Ensure that you are indeed using ``POST``.
   Otherwise, you are querying the user with the name ``login``.
   This will result in a "not authorized" error.

Save the token in ``auth_token``.

.. _authentication_usage:

Using the token
---------------

On any request that requires authentication, send this token via the ``Authorization`` HTTP header.
Use the following format:

.. code-block:: http

    GET /users/user HTTP/1.1
    Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2ODUwNTg0MzMsImlhdCI6MTY4NDQ1MzYzMywic3ViIjoidXNlciIsImp0aSI6bnVsbH0.PBs_YWpIkorTghzTBDHVd3oKer9Vo_YNsgu-yIkG1Cg

Do note that based on server settings, some endpoints may allow access without authenticating.

Renewal
-------
By default, the tokens issued by the server expire after 7 days.
Getting a new token by the end of that period via the normal login API is cumbersome,
as it requires having the user's password.

To solve this problem, Sachet has a renewal API that takes your API token and renews it for you.

Make a ``POST /users/extend`` request with the authentication described in :ref:`authentication_usage`.
The server will respond like this:

.. code-block:: json

    {
        "auth_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2ODUwNTk1MDUsImlhdCI6MTY4NDQ1NDcwNSwic3ViIjoidXNlciIsImp0aSI6InJlbmV3In0.cf4T6U0IJL-ePvYC28QOYHODPi_vkDlaSjA1AdAGDUo",
        "message": "Renewed token.",
        "status": "success",
        "username": "user"
    }

You can now use the new token in ``auth_token`` for future authentication.
This does not revoke your old token.
See :ref:`authentication_log_out` for information on revoking tokens.

.. warning::
   Remember to use the ``POST`` HTTP method and not ``GET``.
   If you use ``GET`` by accident, the server will assume you're trying to read the information of a user called 'extend'.
   This will result in a "not authorized" error.

.. _authentication_log_out:

Signing out
-----------
To revoke a token before expiry, request ``POST /users/logout``.
Use the following request body:

.. code-block:: json

    {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2ODUwNTk3NjIsImlhdCI6MTY4NDQ1NDk2Miwic3ViIjoidXNlciIsImp0aSI6InJlbmV3In0.ZITIK8L5FzLtm-ASwIf6TkTb69z4bsZ8FF0mWee4YI4"
    }

.. warning::

   Ensure that you are indeed using ``POST``.
   Otherwise, you are querying the user with the name ``logout``.
   This will result in a "not authorized" error.
