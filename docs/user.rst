User API
========

.. _user_schema:

User Schema
-----------

In JSON, a User object has the following properties:

.. code-block:: json

    {
        "username": "<username>",
        "password": "<password>",
        "permissions": ["PERMISSION1", "PERMISSION2"],
        "register_date": "2023-05-08T18:57:27.982479"
    }

.. list-table::
    :header-rows: 1
    :widths: 25 25 25 50

    * - Property
      - Type
      - Limits
      - Description
    * - ``username``
      - String
      -
      - User's name. This also acts as an ID.
    * - ``password``
      - String
      - Write-only
      - Password in plain text.
    * - ``permissions``
      - List of String
      -
      - List of permissions (see :ref:`permissions_table`).
    * - ``register_date``
      - DateTime
      - Read-only
      - Time the user registered at.

.. _user_info_api:

User Info API
-------------

The User Info API allows managing users and their permissions.

Sachet implements the following endpoints for this API::

    GET /users/<username>
    PATCH /users/<username>
    PUT /users/<username>

GET
^^^
Requesting ``GET /users/<username>`` returns a JSON object conforming to the :ref:`User schema<user_schema>`.
This contains the information about the specified username.

An example response:

.. code-block:: json

    {
        "permissions": [
            "CREATE",
            "DELETE",
            "LIST",
            "READ"
        ],
        "register_date": "2023-05-08T18:57:27.982479",
        "username": "user"
    }

A user can only read information about themselves, unless they have the :ref:`administrator permission<permissions_table>`.

PATCH
^^^^^

Requesting ``PATCH /users/<username>`` allows modifying some or all fields of a user.
The request body is JSON conforming to the :ref:`User schema<user_schema>`.
Properties may be left out: they won't be modified.

For example, to modify a user's permissions:

.. code-block:: json

    {
        "permissions": [
            "CREATE"
        ]
    }

Only :ref:`administrators<permissions_table>` can request this method.

PUT
^^^

Requesting ``PUT /users/<username>`` completely replaces a user's information.
The request body is JSON conforming to the :ref:`User schema<user_schema>`.
No property may be left out.

For example:

.. code-block:: json

    {
        "permissions": [
            "CREATE"
        ],
        "password": "123",
        "username": "user"
    }

Only :ref:`administrators<permissions_table>` can request this method.

.. _user_list_api:

List API
--------

There is also a User List API::

    GET /users
    POST /users

This API is only accessible to administrators (see :ref:`permissions_table`).

GET
^^^

``GET /users`` is a :ref:`paginated endpoint<pagination>` that returns a list of users.

POST
^^^^

``POST /users`` creates a new user.
The request body must conform to the :ref:`User schema<user_schema>`.
