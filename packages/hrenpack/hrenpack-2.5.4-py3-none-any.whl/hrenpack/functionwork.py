def empty_function(*args, **kwargs):
    pass


def function_if(condition: bool, true, false=empty_function, is_lambda: bool = False):
    if condition:
        return true if is_lambda else true()
    else:
        return false if is_lambda else false()


def lambda_generator(func, *args, **kwargs):
    return lambda: func(*args, **kwargs)


def callable_object(arg):
    return lambda: arg
