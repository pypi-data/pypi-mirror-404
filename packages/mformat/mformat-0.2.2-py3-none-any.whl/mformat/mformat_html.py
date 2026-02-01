#! /usr/local/bin/python3
"""HTML format class."""

# Copyright (c) 2025 - 2026 Tom Björkholm
# MIT License
#

from typing import Optional, Callable
from html import escape
from mformat.mformat_textbased import MultiFormatTextBased
from mformat.mformat_state import MultiFormatState, Formatting
from mformat.mformat import FormatterDescriptor


class MultiFormatHtml(MultiFormatTextBased):
    """HTML format class."""

    def __init__(self,  # pylint: disable=too-many-arguments,too-many-positional-arguments # noqa: E501
                 file_name: str, url_as_text: bool = False,
                 file_exists_callback: Optional[Callable[[str], None]] = None,
                 title: str = 'HTML file', css_file: Optional[str] = None,
                 lang: str = 'en'):
        """Initialize the HtmlFormat class.

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
            title: The title of the HTML file.
            css_file: The name of the CSS file to use.
            lang: The language of the HTML file.
        """
        super().__init__(file_name=file_name, url_as_text=url_as_text,
                         file_exists_callback=file_exists_callback)
        self.title: str = title
        self.css_file: Optional[str] = css_file
        self.lang: str = lang

    @classmethod
    def file_name_extension(cls) -> str:
        """Get the file name extension for the formatter."""
        return '.html'

    @classmethod
    def get_arg_desciption(cls) -> FormatterDescriptor:
        """Get the description of the arguments for the formatter."""
        return FormatterDescriptor(name='html', mandatory_args=[],
                                   optional_args=['title', 'css_file',
                                                  'lang'])

    def _write_file_prefix(self) -> None:
        """Write the file prefix."""
        assert self.file is not None
        self.file.write('<!DOCTYPE html>\n')
        self.file.write(f'<html lang="{self.lang}">\n')
        self.file.write('<head>\n')
        self.file.write('<meta charset="utf-8">\n')
        self.file.write(f'<title>{self.title}</title>\n')
        if self.css_file is not None:
            self.file.write('<link rel="stylesheet" ' +
                            f'href="{self.css_file}">\n')
        self.file.write('</head>\n')
        self.file.write('<body>\n')

    def _write_file_suffix(self) -> None:
        """Write the file suffix."""
        assert self.file is not None
        self.file.write('</body>\n')
        self.file.write('</html>\n')

    def _start_paragraph(self) -> None:
        """Start a paragraph."""
        assert self.file is not None
        self.file.write('<p>\n')

    def _end_paragraph(self) -> None:
        """End a paragraph."""
        assert self.file is not None
        self.file.write('</p>\n')

    def _start_heading(self, level: int) -> None:
        """Start a heading."""
        assert self.file is not None
        self.file.write(f'<h{level}>\n')

    def _end_heading(self, level: int) -> None:
        """End a heading."""
        assert self.file is not None
        self.file.write(f'</h{level}>\n')

    def _write_text(self, text: str, state: MultiFormatState,
                    formatting: Formatting) -> None:
        """Write text into current item (paragraph, bullet list item, etc.).

        Args:
            text: The text to write into the current item.
            state: The state of the current item.
            formatting: The formatting of the text.
        """
        assert self.file is not None
        if formatting.bold:
            text = f'<strong>{text}</strong>'
        if formatting.italic:
            text = f'<em>{text}</em>'
        self.file.write(text)

    def _write_url(self,  # pylint: disable=unused-argument,too-many-arguments,too-many-positional-arguments # noqa: E501
                   url: str, text: Optional[str],
                   state: MultiFormatState,
                   formatting: Formatting) -> None:
        """Write a URL into current item (paragraph, bullet list item...)."""
        assert self.file is not None
        if not text:
            text = url
        text = f'<a href="{url}">{text}</a>'
        if formatting.bold:
            text = f'<strong>{text}</strong>'
        if formatting.italic:
            text = f'<em>{text}</em>'
        self.file.write(text)

    def _start_bullet_list(self, level: int) -> None:
        """Start a bullet list."""
        assert self.file is not None
        assert isinstance(level, int)
        self.file.write('<ul>\n')

    def _end_bullet_list(self, level: int) -> None:
        """End a bullet list."""
        assert self.file is not None
        assert isinstance(level, int)
        self.file.write('</ul>\n')

    def _start_bullet_item(self, level: int) -> None:
        """Start a bullet item."""
        assert self.file is not None
        assert isinstance(level, int)
        self.file.write('<li>')

    def _end_bullet_item(self, level: int) -> None:
        """End a bullet item."""
        assert self.file is not None
        assert isinstance(level, int)
        self.file.write('</li>\n')

    def _start_numbered_list(self, level: int) -> None:
        """Start a numbered list."""
        assert self.file is not None
        assert isinstance(level, int)
        self.file.write('<ol>\n')

    def _end_numbered_list(self, level: int) -> None:
        """End a numbered list."""
        assert self.file is not None
        assert isinstance(level, int)
        self.file.write('</ol>\n')

    def _start_numbered_item(self, level: int, num: int,
                             full_number: str) -> None:
        """Start a numbered item."""
        assert self.file is not None
        assert isinstance(level, int)
        assert isinstance(num, int)
        assert isinstance(full_number, str)
        self.file.write('<li>')

    def _end_numbered_item(self, level: int, num: int) -> None:
        """End a numbered item."""
        assert self.file is not None
        assert isinstance(level, int)
        assert isinstance(num, int)
        self.file.write('</li>\n')

    def _start_table(self, num_columns: int) -> None:
        """Start a table."""
        assert self.file is not None
        assert isinstance(num_columns, int)
        self.file.write('<table border="1">\n')

    def _end_table(self, num_columns: int, num_rows: int) -> None:
        """End a table."""
        assert self.file is not None
        assert isinstance(num_columns, int)
        assert isinstance(num_rows, int)
        self.file.write('</table>\n')

    def _write_table_first_row(self, first_row: list[str],
                               formatting: Formatting) -> None:
        """Write the first row of a table."""
        assert self.file is not None
        assert self.table is not None
        self._write_table_row(row=first_row, formatting=formatting,
                              row_number=0)

    def _write_table_row(self, row: list[str],
                         formatting: Formatting, row_number: int) -> None:
        """Write a row of a table."""
        assert self.file is not None
        assert self.table is not None
        self.file.write('<tr>\n')
        for cell in row:
            if formatting.bold:
                cell = f'<strong>{cell}</strong>'
            if formatting.italic:
                cell = f'<em>{cell}</em>'
            self.file.write(f'<td>{cell}</td>\n')
        self.file.write('</tr>\n')

    def _start_code_block(self, programming_language: Optional[str]) -> None:
        """Start a code block."""
        assert self.file is not None
        assert programming_language is None or \
            isinstance(programming_language, str)
        self.file.write('<pre><code>\n')
        if programming_language is not None:
            span = f'<span class="language-{programming_language}">'
            self.file.write(span)

    def _end_code_block(self, programming_language: Optional[str]) -> None:
        """End a code block."""
        assert self.file is not None
        assert programming_language is None or \
            isinstance(programming_language, str)
        if programming_language is not None:
            self.file.write('</span>\n')
        self.file.write('</code></pre>\n')

    def _write_code_block(self, text: str,
                          programming_language: Optional[str]) -> None:
        """Write a code block."""
        assert self.file is not None
        assert programming_language is None or \
            isinstance(programming_language, str)
        # Text is already encoded via _encode_text in base class
        self.file.write(text)

    def _encode_text(self, text: str) -> str:
        """Encode text (escape special characters)."""
        return escape(text, quote=True)
