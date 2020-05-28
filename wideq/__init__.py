"""Reverse-engineered client for the LG SmartThinQ API.
"""
import uuid

__version__ = '1.4.0'


def as_list(obj):
    """Wrap non-lists in lists.

    If `obj` is a list, return it unchanged. Otherwise, return a
    single-element list containing it.
    """

    if isinstance(obj, list):
        return obj
    else:
        return [obj]


def gen_uuid():
    return str(uuid.uuid4())
