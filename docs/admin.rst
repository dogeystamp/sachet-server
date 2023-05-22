Admin API
=========

The administration API ``/admin`` helps the administrator user manage the Sachet server.

An important component that is not within this endpoint is user management.
See :ref:`user_info_api` and :ref:`user_list_api` for information about managing users.

Server settings
---------------

Sachet has a server settings API::
    
    GET /admin/settings
    PATCH /admin/settings
    PUT /admin/settings

Currently, server settings are represented by the following object:

.. code-block:: json

    {
        "default_permissions": ["PERMISSION1", "PERMISSION2"]
    }

.. _admin_anon_perms:

Anonymous permissions
^^^^^^^^^^^^^^^^^^^^^

Anonymous permissions (``default_permissions`` in the schema) are given to clients that do not authenticate.
It is an array of strings as described by :ref:`permissions_table`.

This can be useful, for example, to publish a file to the Internet.
If the Read shares permission is enabled in anonymous permissions, anyone can read a share if given the link to it.
