#! /usr/local/bin/python3
"""Markdown format class."""

# Copyright (c) 2025 - 2026 Tom Björkholm
# MIT License
#

from copy import deepcopy
from typing import Optional, Callable
from mformat.mformat_textbased import MultiFormatTextBased
from mformat.mformat_state import MultiFormatState, Formatting
from mformat.mformat import FormatterDescriptor


def split_whitespace(text: str) -> tuple[str, str, str]:
    """Split a string into leading, stripped, and trailing whitespace."""
    if not text:
        return '', '', ''
    stripped = text.strip()
    if not stripped:
        return text, '', ''
    if stripped == text:
        return '', stripped, ''
    leading = text[:len(text) - len(text.lstrip())]
    trailing = text[len(text.rstrip()):]
    return leading, stripped, trailing


class MultiFormatMd(MultiFormatTextBased):
    """Markdown format class."""

    def __init__(self, file_name: str, url_as_text: bool = False,
                 file_exists_callback: Optional[Callable[[str], None]] = None):
        """Initialize the MdFormat class.

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

    @classmethod
    def file_name_extension(cls) -> str:
        """Get the file name extension for the formatter."""
        return '.md'

    @classmethod
    def get_arg_desciption(cls) -> FormatterDescriptor:
        """Get the description of the arguments for the formatter."""
        return FormatterDescriptor(name='md', mandatory_args=[],
                                   optional_args=[])

    def _write_file_prefix(self) -> None:
        """Write the file prefix."""

    def _write_file_suffix(self) -> None:
        """Write the file suffix."""

    def _start_paragraph(self) -> None:
        """Start a paragraph."""
        assert self.file is not None
        self._empty_line_before()

    def _end_paragraph(self) -> None:
        """End a paragraph."""
        assert self.file is not None
        self.file.write('\n')

    def _empty_line_before(self) -> None:
        """Make sure there is an empty line before next item."""
        assert self.file is not None
        preceeding = self._get_last_chars_written(num_chars=2)
        if preceeding in ('\n\n', ''):
            pass
        elif preceeding[-1] == '\n':
            self.file.write('\n')
        else:
            self.file.write('\n\n')

    def _start_heading(self, level: int) -> None:
        """Start a heading."""
        assert self.file is not None
        self._empty_line_before()
        self.file.write(f'{"#" * level} ')

    def _end_heading(self, level: int) -> None:
        """End a heading."""
        assert self.file is not None
        self.file.write('\n')

    @staticmethod
    def _format_text(text: str, formatting: Formatting) -> str:
        """Format text with bold and italic."""
        pre, stripped, post = split_whitespace(text)
        if not stripped:
            return text
        if formatting.bold:
            stripped = f'**{stripped}**'
        if formatting.italic:
            stripped = f'*{stripped}*'
        return pre + stripped + post

    def _write_text(self,  # pylint: disable=unused-argument,too-many-arguments,too-many-positional-arguments # noqa: E501
                    text: str, state: MultiFormatState,
                    formatting: Formatting) -> None:
        """Write text into current item (paragraph, bullet list item, etc.).

        Args:
            text: The text to write into the current item.
            state: The state of the current item.
            formatting: The formatting of the text.
        """
        assert self.file is not None
        self.file.write(self._format_text(text, formatting))

    def _write_url(self,  # pylint: disable=unused-argument,too-many-arguments,too-many-positional-arguments # noqa: E501
                   url: str, text: Optional[str],
                   state: MultiFormatState,
                   formatting: Formatting) -> None:
        """Write a URL into current item (paragraph, bullet list item...)."""
        assert self.file is not None
        if not text:
            text = url
        text = f'[{text}]({url})'
        self.file.write(self._format_text(text, formatting))

    def _start_bullet_list(self, level: int) -> None:
        """Start a bullet list."""
        assert self.file is not None
        assert isinstance(level, int)

    def _end_bullet_list(self, level: int) -> None:
        """End a bullet list."""
        assert self.file is not None
        assert isinstance(level, int)

    def _indent(self, level: int) -> str:
        """Get the indentation for a level."""
        assert self.file is not None
        assert isinstance(level, int)
        return 2*(level-1)*' '

    def _start_bullet_item(self, level: int) -> None:
        """Start a bullet item."""
        assert self.file is not None
        assert isinstance(level, int)
        self._empty_line_before()
        self.file.write(self._indent(level) + '- ')

    def _end_bullet_item(self, level: int) -> None:
        """End a bullet item."""
        assert self.file is not None
        assert isinstance(level, int)
        self.file.write('\n')

    def _start_numbered_list(self, level: int) -> None:
        """Start a numbered list."""
        assert self.file is not None
        assert isinstance(level, int)

    def _end_numbered_list(self, level: int) -> None:
        """End a numbered list."""
        assert self.file is not None
        assert isinstance(level, int)

    def _start_numbered_item(self, level: int, num: int,
                             full_number: str) -> None:
        """Start a numbered item."""
        assert self.file is not None
        assert isinstance(level, int)
        assert isinstance(num, int)
        self._empty_line_before()
        self.file.write(self._indent(level) + full_number + ' ')

    def _end_numbered_item(self, level: int, num: int) -> None:
        """End a numbered item."""
        assert self.file is not None
        assert isinstance(level, int)
        assert isinstance(num, int)
        self.file.write('\n')

    def _start_code_block(self, programming_language: Optional[str]) -> None:
        """Start a code block."""
        assert self.file is not None
        if programming_language is None:
            programming_language = 'text'
        self.file.write(f'\n````{programming_language}\n')

    def _end_code_block(self, programming_language: Optional[str]) -> None:
        """End a code block."""
        assert self.file is not None
        assert programming_language is None or \
            isinstance(programming_language, str)
        self.file.write('\n````\n')

    def _write_code_block(self, text: str,
                          programming_language: Optional[str]) -> None:
        """Write a code block."""
        assert self.file is not None
        assert programming_language is None or \
            isinstance(programming_language, str)
        self.file.write(text)

    def _start_table(self, num_columns: int) -> None:
        """Start a table."""
        assert self.file is not None
        assert isinstance(num_columns, int)
        self.file.write('\n')

    def _end_table(self, num_columns: int, num_rows: int) -> None:
        """End a table."""
        assert self.file is not None
        assert isinstance(num_columns, int)
        assert isinstance(num_rows, int)
        self.file.write('\n')

    def _write_table_first_row(self, first_row: list[str],
                               formatting: Formatting) -> None:
        """Write the first row of a table."""
        assert self.file is not None
        assert self.table is not None
        self._write_table_row(row=first_row, formatting=formatting,
                              row_number=0)
        col_lines = [width*'-' for width in self.table.column_widths]
        line = '|-' + '-|-'.join(col_lines) + '-|'
        self.file.write(line + '\n')

    def _write_table_row(self, row: list[str],
                         formatting: Formatting, row_number: int) -> None:
        """Write a row of a table."""
        assert self.file is not None
        assert self.table is not None
        if len(row) != self.table.number_of_columns:
            err = f'Row {row_number} has {len(row)} columns, but '
            err += f'table has {self.table.number_of_columns} columns.'
            raise ValueError(err)
        # Make a copy of the row to avoid modifying the original row.
        local_row = deepcopy(row)
        if formatting.bold or formatting.italic:
            local_row = [self._format_text(cell, formatting)
                         for cell in local_row]
        # Update column widths to account for formatted text
            self._update_table_column_widths(row=local_row)
        local_row = [cell.ljust(width) for cell, width in
                     zip(local_row, self.table.column_widths)]
        self.file.write(f'| {" | ".join(local_row)} |\n')

    def _encode_text(self, text: str) -> str:
        """Encode text (escape special characters) for Markdown.

        Uses context-aware escaping based on Markdown syntax rules.
        Characters are only escaped when they could be interpreted as
        Markdown syntax in their specific context.
        """
        if not text:
            return text
        if self.state == MultiFormatState.CODE_BLOCK:
            return text.replace('````',
                                '\\`\\`\\`\\`').replace('```',
                                                        '\\`\\`\\`')
        result: list[str] = []
        n = len(text)
        for i, char in enumerate(text):
            prev_char = text[i - 1] if i > 0 else ''
            next_char = text[i + 1] if i + 1 < n else ''
            result.append(self._escape_char(char, prev_char, next_char))
        return ''.join(result)

    def _escape_char(self, char: str, prev_char: str, next_char: str) -> str:
        """Escape a single character based on context.

        Args:
            char: The character to potentially escape.
            prev_char: The previous character ('' if at start).
            next_char: The next character ('' if at end).

        Returns:
            The character, escaped if necessary.
        """
        # Characters that always need escaping
        always_escape = '\\`[]{}<|'
        if char in always_escape:
            return '\\' + char
        # Characters with simple context rules
        simple_context = {
            '(': '\\(' if prev_char == ']' else char,
            '!': '\\!' if next_char == '[' else char,
            '~': '\\~' if prev_char == '~' or next_char == '~' else char,
        }
        if char in simple_context:
            return simple_context[char]
        # Characters requiring line-start awareness
        at_line_start = prev_char in ('', '\n')
        return self._escape_line_context_char(char, prev_char, next_char,
                                              at_line_start)

    def _escape_line_context_char(
            self, char: str, prev_char: str, next_char: str,
            at_line_start: bool) -> str:
        """Escape characters that depend on line position context.

        Args:
            char: The character to potentially escape.
            prev_char: The previous character ('' if at start).
            next_char: The next character ('' if at end).
            at_line_start: True if at the start of a line.

        Returns:
            The character, escaped if necessary.
        """
        if char == '>':
            return self._escape_greater_than(prev_char, at_line_start)
        if char == '#':
            return '\\#' if at_line_start else char
        if char in '-+':
            return self._escape_list_marker(char, next_char, at_line_start)
        if char in '*_':
            return self._escape_emphasis(char, prev_char, next_char,
                                         at_line_start)
        if char == '=':
            return self._escape_equals(next_char, at_line_start)
        return char

    def _escape_greater_than(self, prev_char: str,
                             at_line_start: bool) -> str:
        """Escape > for blockquotes and HTML."""
        if at_line_start or prev_char == '<':
            return '\\>'
        return '>'

    def _escape_list_marker(self, char: str, next_char: str,
                            at_line_start: bool) -> str:
        """Escape - or + for list markers and horizontal rules."""
        if not at_line_start:
            return char
        if next_char in (' ', '\t', '') or next_char == char:
            return '\\' + char
        return char

    def _escape_emphasis(self, char: str, prev_char: str, next_char: str,
                         at_line_start: bool) -> str:
        """Escape * or _ for emphasis markers."""
        # Check for list item or horizontal rule at line start
        if at_line_start and char == '*':
            if next_char in (' ', '\t', '') or next_char == '*':
                return '\\*'
        elif at_line_start and next_char == char:
            return '\\' + char
        # Check for emphasis at word boundaries
        if self._is_emphasis_position(prev_char, next_char):
            return '\\' + char
        return char

    def _escape_equals(self, next_char: str, at_line_start: bool) -> str:
        """Escape = for setext heading underlines."""
        if at_line_start and next_char in ('=', ''):
            return '\\='
        return '='

    def _is_emphasis_position(self, prev_char: str, next_char: str) -> bool:
        """Check if position could be an emphasis delimiter.

        Based on CommonMark flanking rules - emphasis delimiters are
        recognized at word boundaries (adjacent to whitespace, punctuation,
        or string boundaries).

        Args:
            prev_char: Character before the potential delimiter ('' if none).
            next_char: Character after the potential delimiter ('' if none).

        Returns:
            True if the position could be an emphasis delimiter.
        """
        prev_is_boundary = not prev_char or not prev_char.isalnum()
        next_is_boundary = not next_char or not next_char.isalnum()
        return prev_is_boundary or next_is_boundary
