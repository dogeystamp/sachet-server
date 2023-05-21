Permissions
===========

Sachet offers a selection of permissions that can be assigned to users,
which manage their access to certain endpoints.

Serialization
-------------
In Sachet's JSON API, permissions are serialized as an array of string codes.
These codes are documented in :ref:`permissions_table`.

For instance, here is an example output for ``GET /users/user``:

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

.. _permissions_table:

Table of permissions
--------------------

The following is a table of permissions Sachet offers, and what they do:

.. list-table::
    :widths: 25 25 50
    :header-rows: 1

    * - Permission
      - Code
      - Description
    * - Create shares
      - ``CREATE``
      - Allows uploading files to Sachet.
    * - Modify shares
      - ``MODIFY``
      - Allows users to modify their own shares' contents and metadata.
    * - Delete shares
      - ``DELETE``
      - Allows users to delete any share.
    * - Lock shares
      - ``LOCK``
      - Allows users to lock and unlock shares.
    * - List shares
      - ``LIST``
      - Allows users to list all shares from all users.
    * - Read shares
      - ``READ``
      - Allows users to read any share.
    * - Administration
      - ``ADMIN``
      - Allows creating users and managing their permissions.
