#!/usr/bin/env python3

#
# Copyright (c) 2018 - 2026 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Script to determine the supported web browser variant.

It looks for QtWebEngine. It reports the variant found or the string 'None' if
it is absent.
"""

import importlib.util
import sys

variant = (
    "QtWebEngine"
    if (
        bool(importlib.util.find_spec("PyQt6"))
        and bool(importlib.util.find_spec("PyQt6.QtWebEngineWidgets"))
    )
    else "None"
)
print(variant)  # noqa: T201, M-801

sys.exit(0)
