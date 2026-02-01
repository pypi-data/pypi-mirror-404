
def unpack(value):
    """Return a three-tuple of (data, code, headers)"""
    if not isinstance(value, tuple):
        return value, 200, {}

    if len(value) == 3:
        return value
    elif len(value) == 2:
        data, code = value
        return data, code, {}
    else:
        return value, 200, {}
