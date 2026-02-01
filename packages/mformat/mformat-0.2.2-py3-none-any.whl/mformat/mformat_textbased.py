#! /usr/local/bin/python3
"""Base class for all text based format classes."""

# Copyright (c) 2025 - 2026 Tom Björkholm
# MIT License
#

import io
from typing import TextIO, Optional, Callable
from mformat.mformat import MultiFormat


class MultiFormatTextBased(MultiFormat):
    """Base class for all text based format classes."""

    def __init__(self, file_name: str, url_as_text: bool = False,
                 file_exists_callback: Optional[Callable[[str], None]] = None):
        """Initialize the TextBasedFormat class.

        Args:
            file_name: The name of the file to write to.
            url_as_text: Format URLs as text not clickable URLs.
            file_exists_callback: A callback function to call if the file
                                  already exists. Return to allow the file to
                                  be overwritten. Raise an exception to prevent
                                  the file from being overwritten.
                                  (May for instance save existing file as
                                  backup.)
                                  (Default is to raise an exception.)
        """
        super().__init__(file_name=file_name, url_as_text=url_as_text,
                         file_exists_callback=file_exists_callback)
        self.file: Optional[TextIO] = None

    def open(self) -> None:
        """Open the file.

        Avoid using this method directly.
        Use as a context manager instead, using a with statement.
        """
        self.file = open(self.file_name,  # pylint: disable=consider-using-with
                         mode='w+t', encoding='utf-8')

    def _close(self) -> None:
        """Close the file.

        Avoid using this method directly.
        Use as a context manager instead, using a with statement.
        """
        if self.file is None:
            return
        self.file.close()
        self.file = None

    def _get_last_chars_written(self, num_chars: int) -> str:
        """Get the last characters written to the file.

        Keep the file pointer at the same position, i.e. at the end of the
        file, so that we can continue writing after the last characters.
        Returns the last characters written to the file.
        """
        assert self.file is not None
        assert num_chars > 0
        cur_pos = self.file.tell()
        number_of_chars = min(num_chars, cur_pos)
        self.file.seek(cur_pos - number_of_chars, io.SEEK_SET)
        last_chars = self.file.read(number_of_chars)
        self.file.seek(cur_pos, io.SEEK_SET)
        return last_chars
