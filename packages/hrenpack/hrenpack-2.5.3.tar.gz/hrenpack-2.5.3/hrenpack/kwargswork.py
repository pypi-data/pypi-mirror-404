from hrenpack.listwork import dict_keyf


def kwarg_return(kwargs: dict, key: str, false):
    return dict_keyf(kwargs, key, false)


def kwarg_function(kwargs: dict, key: str, true, false):
    if key in kwargs:
        true()
    else:
        false()


def kwarg_kwargs(**kwargs):
    return kwargs


def get_kwarg(kwargs: dict, key: str, default=None, raise_error: bool = True, delete: bool = False):
    if default:
        raise_error = False
    if raise_error and key not in kwargs:
        raise KeyError(key)
    output = kwargs.get(key, default)
    if delete and key in kwargs:
        del kwargs[key]
    return output
