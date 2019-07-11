from typing import TypeVar

from .client import Device


T = TypeVar('T', bound=Device)


def lookup_enum(attr: str, data: dict, device: T):
    """Looks up an enum value for the provided attr.

    :param attr: The attribute to lookup in the enum.
    :param data: The JSON data from the API.
    :param device: A sub-class instance of a Device.
    :returns: The enum value.
    """
    return device.model.enum_name(attr, data[attr])


def lookup_reference(attr: str, data: dict, device: T) -> str:
    """Look up a reference value for the provided attribute.

    :param attr: The attribute to find the value for.
    :param data: The JSON data from the API.
    :param device: A sub-class instance of a Device.
    :returns: The looked up value.
    """
    value = device.model.reference_name(attr, data[attr])
    if value is None:
        return 'Off'
    return value
