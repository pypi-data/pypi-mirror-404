def freeze(x):
    if isinstance(x, dict):
        return frozenset((k, freeze(v)) for k, v in x.items())
    if isinstance(x, (list, tuple)):
        return tuple(freeze(i) for i in x)
    if isinstance(x, set):
        return frozenset(freeze(i) for i in x)
    return x  # antar hashbart