#! /usr/local/bin/python3
"""Enum for the state of the multi file format."""

# Copyright (c) 2025 - 2026 Tom Björkholm
# MIT License
#

from enum import IntEnum, auto
from typing import NamedTuple


class MultiFormatState(IntEnum):
    """Enum for the state of the multi file format."""

    EMPTY = auto()
    HEADING = auto()
    PARAGRAPH = auto()
    PARAGRAPH_END = auto()
    BULLET_LIST = auto()
    BULLET_LIST_ITEM = auto()
    NUMBERED_LIST = auto()
    NUMBERED_LIST_ITEM = auto()
    TABLE = auto()
    CODE_BLOCK = auto()
    CLOSED = auto()


class Formatting(NamedTuple):
    """Formatting information."""

    bold: bool
    italic: bool


class FormattingWithWS(NamedTuple):
    """Formatting information with whitespace."""

    formatting: Formatting
    smart_ws: bool
