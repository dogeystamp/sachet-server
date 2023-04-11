class Storage:
    """Generic storage interface.

    Raises
    ------
    OSError
        If the storage could not be initialized.
    """

    def list_files(self):
        """Lists all files.

        Returns
        -------
        list of File

        """

        pass

    def get_file(self, name):
        """Return a File handle for a given file.

        The file will be created if it does not exist yet.

        Parameters
        ----------
        name : str
            Filename to access.

        """

        pass

    class File:
        """Handle for a file.

        Do not instantiate this; use `Storage.get_file()`.

        Attributes
        ----------
        name : str
            Filename
        """

        def open(self, mode="r"):
            """Open file for reading/writing.

            Parameters
            ----------
            mode : str, optional
                Mode of access (same as `open()`.)

            Returns
            -------
                _io.TextIOWrapper
                    Stream to access the file (just like the builtin `open()`.)

            """

            pass

        def delete(self):
            """Delete file."""

            pass

        def rename(self, new_name):
            """Rename a file.

            Parameters
            ----------
            new_name : str
                New name for the file.
            """

            pass


from .filesystem import FileSystem
