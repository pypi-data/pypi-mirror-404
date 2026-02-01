#! /usr/local/bin/python3
"""Register the formats defined in the package with the factory."""

# Copyright (c) 2025 - 2026 Tom Björkholm
# MIT License
#

from mformat.mformat import MultiFormat
from mformat.mformat_html import MultiFormatHtml
from mformat.mformat_md import MultiFormatMd


def register_formats_in_pkg() -> list[type[MultiFormat]]:
    """Get formats defined in the package to register with the factory."""
    ret: list[type[MultiFormat]] = [MultiFormatHtml, MultiFormatMd]
    try:
        # try to also register the formats defined in the extension package
        # pylint: disable=import-outside-toplevel,wrong-import-order
        from mformat_ext.reg_extpkg_formats import register_formats_in_ext_pkg
        ret += register_formats_in_ext_pkg()
    except (ImportError, ModuleNotFoundError):
        pass  # mformat_ext package not installed
    return ret
