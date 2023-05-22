Files API
=========

Overview
--------
The file upload process essentially works as follows:

#. ``POST /files`` with the metadata to create a share.
   This will return an URL with the share you just created.
   (See :ref:`files_list_api`.)
#. ``POST /files/<uuid>/content`` (the UUID is in the URL from the previous step) to upload the actual data of the share. (See :ref:`files_content_api`.)
#. ``GET /files/<uuid>/content`` to read the share.

Share modification is done with ``PUT /files/<uuid>/content``.

Shares can be locked, which means they can't be modified or deleted.
See :ref:`files_lock_api` for more information.

.. note::

   All data uploads are chunked: see :ref:`files_chunked_upload`.

.. _files_schema:

File Schema
-----------

In JSON, a file share has the following properties::

    {
        "file_name": "file.txt",
        "initialized": true,
        "locked": false,
        "owner_name": "user",
        "share_id": "9ae90f06-a751-409c-a9fe-8277575b9914"
    }

.. list-table::
    :header-rows: 1
    :widths: 25 25 25 50

    * - Property
      - Type
      - Limits
      - Description
    * - ``file_name``
      - String
      -
      - The file's name (with extension).
    * - ``initialized``
      - Boolean
      - Read-only
      - Shows if content exists for this share.
    * - ``locked``
      - Boolean
      - Read-only
      - Shows if share is locked (see :ref:`files_lock_api`.)
    * - ``owner_name``
      - string
      -
      - Username of the owner.
    * - ``share_id``
      - string
      - Read-only
      - UUID that uniquely identifies this share.

.. note::

   Share ownership can be changed by changing ``owner_name``.
   Do note that setting it to ``null`` is equivalent to :ref:`unauthenticated users<admin_anon_perms>` owning the share.

.. _files_metadata_api:

Metadata API
------------

The File Metadata API allows managing file shares' metadata.

Sachet implements the following endpoints for this API::

    GET /files/<file_uuid>
    PATCH /files/<file_uuid>
    PUT /files/<file_uuid>

GET
^^^
Requesting ``GET /files/<file_uuid>`` returns a JSON object conforming to the :ref:`File schema<files_schema>`.
This contains the information about the share with the specified UUID.

An example response:

.. code-block:: json

    {
        "file_name": "file.txt",
        "initialized": true,
        "locked": false,
        "owner_name": "user",
        "share_id": "9ae90f06-a751-409c-a9fe-8277575b9914"
    }

This method requires the :ref:`read<permissions_table>` permission.

PATCH
^^^^^

Requesting ``PATCH /files/<file_uuid>`` allows modifying some or all fields of the share's metadata.
The request body is JSON conforming to the :ref:`File schema<files_schema>`.
Properties may be left out: they won't be modified.

For example, to modify a share's filename:

.. code-block:: json

    {
        "file_name": "foobar.mp3"
    }

This method requires the :ref:`modify<permissions_table>` permission.

PUT
^^^

Requesting ``PUT /files/<file_uuid>`` completely replaces a share's metadata.
The request body is JSON conforming to the :ref:`File schema<files_schema>`.
No property may be left out.

For example:

.. code-block:: json

    {
        "file_name": "foobar.mp4",
        "owner_name": "user"
    }

.. note::

    The permissions from the schema that are missing here are read-only.

.. _files_list_api:

List API
--------

The File List API allows listing shares and creating new ones::

    GET /files
    POST /files

GET
^^^

``GET /files`` is a :ref:`paginated endpoint<pagination>` that returns a list of shares.

To access this endpoint, a user needs the :ref:`list shares<permissions_table>` permission.

POST
^^^^

``POST /files`` creates a new share.
The request body must conform to the :ref:`File schema<files_schema>`.

To access this endpoint, a user needs the :ref:`create shares<permissions_table>` permission.

.. note::
   
    The share created here is empty, and only contains metadata.
    See :ref:`files_content_api` for information on uploading content.

Upon success, the server will respond like this:

.. code-block:: json

    {
      "status": "success",
      "url": "/files/d9eafb5e-af48-40ec-b6fd-f7ea99e6d990"
    }

The ``url`` field represents the share you just created.
It can be used in further requests to upload content to the share.

.. _files_content_api:

Content API
-----------

The File Content API allows managing file shares' contents.

Sachet implements the following endpoints for this API::

    POST /files/<file_uuid>/content
    PUT /files/<file_uuid>/content
    GET /files/<file_uuid>/content

POST
^^^^

``POST /files/<file_uuid>/content`` initializes the content of an empty share.
This endpoint requires the :ref:`create shares<permissions_table>` permission.

.. note::

    You must first create a share before initializing it: see :ref:`files_list_api` for information about creation.

Uploads must be chunked (see :ref:`files_chunked_upload`).

To modify the contents of an existing share, use ``PUT`` instead.

PUT
^^^^

``PUT /files/<file_uuid>/content`` modifies the content of an existing share.
This endpoint requires the :ref:`modify shares<permissions_table>` permission.

.. note::

    You must initialize a share's content using ``POST`` before modifying it.

Uploads must be chunked (see :ref:`files_chunked_upload`).

GET
^^^^

``GET /files/<file_uuid>/content`` reads the contents of a share.
This endpoint requires the :ref:`read shares<permissions_table>` permission.

This endpoint supports `HTTP Range <https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Range>`_ headers.

.. _files_chunked_upload :

Chunked upload protocol
^^^^^^^^^^^^^^^^^^^^^^^
To allow for uploading large files reliably, Sachet requires that you upload files in chunks.

Partial uploads do not affect the state of the share;
a new file exists only once all chunks are uploaded.

Chunks are ordered by their index.
Once an upload finishes, they are combined in that order to form the new file.

The server will respond with ``200 OK`` when chunks are sent.
When the final chunk is sent, and the upload is completed,
the server will instead respond with ``201 Created``.

Every chunk has the following schema:

.. _files_chunk_schema:

.. code-block::

    dztotalchunks = 3
    dzchunkindex = 2
    dzuuid = "unique_id"
    upload = <binary data>

.. note::

   This data is sent via a ``multipart/form-data`` request; it's not JSON.

.. list-table::
    :header-rows: 1
    :widths: 25 25 50

    * - Property
      - Type
      - Description
    * - ``dztotalchunks``
      - Integer
      - Total number of chunks the client will send.
    * - ``dzchunkindex``
      - Integer
      - Number of the chunk being sent.
    * - ``dzuuid``
      - String
      - ID which is the same for all chunks in a single upload.
    * - ``upload``
      - Binary data (file)
      - Data contained in this chunk.

.. _files_lock_api:

Lock API
--------

Files can be locked and unlocked.
When locked, a share can not be modified or deleted.

.. note::

   When attempting illegal actions on a locked share, the server will respond ``423 Locked``.

The following API is used::

    POST /files/<uuid>/lock
    POST /files/<uuid>/unlock

A user needs the :ref:`lock permission<permissions_table>` to access this API.

To query whether a file is locked or not, see :ref:`files_metadata_api`.
