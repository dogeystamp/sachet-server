.. _pagination:

Paginated APIs
==============

Some APIs in Sachet might return lots of data.
Because this is often a lot to handle, Sachet will use pagination on some endpoints.

For example, let's say we want to list all shares on the server.

To do this, we'll run ``GET /files?page=1&per_page=3``.

Paginated APIs on Sachet require the following parameters:

* ``page`` : the number of the page we want to query;
* ``per_page`` : the number of items per page we receive.

For our example, the server might respond like this (fields removed for brevity):

.. code-block:: json

   {
       "data": [
           {
               "file_name": "file1",
               "share_id": "339ce639-cf54-4acf-9620-c915c5dce406"
           },
           {
               "file_name": "file2",
               "share_id": "9ae90f06-a751-409c-a9fe-8277575b9914"
           },
           {
               "file_name": "file3",
               "share_id": "4f8e41ab-3327-4fc1-a52b-8951ac5c641f"
           }
       ],
       "next": 2,
       "pages": 3,
       "prev": null
    }

Our query's result is returned as an array in ``data``.
As we requested, we have 3 items on the first page.

There's also two extra fields ``next`` and ``prev``,
which help us navigate to other pages.
Since we're on the first page, there is no previous page, which is why ``prev`` is empty.

If we wished to go to the next page, we'd make the same request with the new page number.

The ``pages`` field is the total number of pages there is in this query.
That is, page 3 is the last page in this example.
