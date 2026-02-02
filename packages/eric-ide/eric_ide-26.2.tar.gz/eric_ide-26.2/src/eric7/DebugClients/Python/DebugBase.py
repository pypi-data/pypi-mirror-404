#
# Copyright (c) 2002 - 2026 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module switching between the older tracing debugger and the modern event based debugger.
"""

import sys

try:
    if "--settrace" in sys.argv:
        from debug_settrace import DebugBase, printerr, setRecursionLimit
        # __IGNORE_WARNING__
    else:
        from debug_monitor import DebugBase, printerr, setRecursionLimit
        # __IGNORE_WARNING__
except ImportError:
    from debug_settrace import DebugBase, printerr, setRecursionLimit  # noqa: F401
    # __IGNORE_WARNING__
