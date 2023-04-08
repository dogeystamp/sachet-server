class Storage:
    """Generic storage interface.

    Raises:
        OSError if SACHET_FILE_DIR could not be opened as a directory.
    """

    def create(self, name):
        """Create file along with the metadata.

        Raises:
            OSError if the file already exists.
        """

        pass

    def open(self, name, mode="r"):
        """Open a file for reading/writing.

        Raises:
            OSError if the file does not exist.

        Returns:
            Stream to access file (similar to open()'s handle.)
        """

        pass

    def read_metadata(self, name):
        """Get metadata for a file.

        Raises:
            OSError if the file does not exist.
        """

        pass

    def write_metadata(self, name, data):
        """Set metadata for a file.

        Raises:
            OSError if the file does not exist.
        """

        pass

    def delete(self, name):
        """Delete file and associated metadata.

        Raises:
            OSError if the file does not exist.
        """

        pass

    def rename(self, name, new_name):
        """Rename a file.

        Raises:
            OSError if the file does not exist.
        """

        pass

    def list_files(self):
        """Lists all files."""

        pass


from .filesystem import FileSystem
