Files API
=========

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
      - Shows if share is locked.
    * - ``owner_name``
      - string
      -
      - Username of the owner.
    * - ``share_id``
      - string
      - Read-only
      - UUID that uniquely identifies this share.

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

Content API
-----------

The File Content API allows managing file shares' contents.

Sachet implements the following endpoints for this API::

    POST /files/<file_uuid>/content
    PUT /files/<file_uuid>/content
    GET /files/<file_uuid>/content

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

.. _files_chunk_schema :

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
