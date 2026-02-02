#
# Copyright (c) 2025 - 2026 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing network related utility functions.
"""


def ipv6AddressScope(address):
    """
    Function to determine the scope of an IPv6 address.

    @param address IPv6 address
    @type str
    @return address scope
    @rtype str
    """
    address = address.lower()
    if address.startswith("fe80"):
        return "Link-Local Scope"
    if address.startswith("fec"):
        return "Site-Local Scope"
    if address.startswith("ff"):
        return "Multicast Scope"
    if address.startswith(("fc", "fd")):
        return "Unique-Local Scope"
    return "Global Scope"
