#! /usr/local/bin/python3
"""Register the formats defined in the ext package with the factory."""

# Copyright (c) 2025 - 2026 Tom Björkholm
# MIT License
#

from mformat_ext.mformat_docx import MultiFormatDocx
from mformat_ext.mformat_odt import MultiFormatOdt
from mformat.mformat import MultiFormat


def register_formats_in_ext_pkg() -> list[type[MultiFormat]]:
    """Get formats defined in the ext package to register with the factory."""
    ret: list[type[MultiFormat]] = [MultiFormatDocx, MultiFormatOdt]
    return ret
