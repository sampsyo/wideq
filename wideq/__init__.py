"""Reverse-engineered client for the LG SmartThinQ API."""
# These imports are for backwards compatiability with previous versions.
from .ac import ACDevice, ACFanSpeed, ACMode, ACOp, ACStatus  # noqa
from .errors import (  # noqa
    APIError, MonitorError, NotConnectedError, NotLoggedInError, TokenError)

__version__ = '1.0.1'
