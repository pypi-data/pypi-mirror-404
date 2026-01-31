"""Structure module."""


class dotdict(dict):  # noqa: N801
    """Dotdict class."""

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
