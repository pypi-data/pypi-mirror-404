"""Module to retrieve the MAC address of the primary network interface."""

from getmac import get_mac_address as gma


class MacAddressError(Exception):
    """Exception raised when MAC address cannot be retrieved."""

    pass


def get_mac_address() -> str:
    """Get the MAC address of the primary network interface."""

    mac_addr = gma()
    if not mac_addr:
        raise MacAddressError("Could not retrieve MAC address.")
    return mac_addr
