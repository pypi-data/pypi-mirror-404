import warnings
from typing import Union, Literal

stb = Union[str, bool]
tdl = Union[tuple, list, dict]
_any, _all = any, all


def booltest(bull: stb) -> None:
    if bull.lower() == 'true' or bull.lower() == 'false' or bull is True or bull is False:
        pass
    else:
        raise TypeError("Данная функция может работать только с булевыми значениями")


def str_to_bool(input: stb) -> bool:
    if type(input) is bool:
        return input
    elif input.lower() == 'true' or int(input) == 1:
        return True
    elif input.lower() == 'false' or int(input) == 0:
        return False
    else:
        raise TypeError("Данная функция может работать только с булевыми значениями")


def bool_list_count(input: tdl) -> dict:
    def TF(bull: bool, dict_tf: dict):
        if bull:
            dict_tf[True] += 1
        else:
            dict_tf[False] += 1

    TrueFalse = {True: 0, False: 0}
    if type(input) is dict:
        for key in input:
            value = input[key]
            booltest(value)
            TF(value, TrueFalse)
    else:
        for b in input:
            booltest(b)
            TF(b, TrueFalse)
    return TrueFalse


def Fand(*questions: bool):
    warnings.warn('This function is deprecated, use all() instead', DeprecationWarning, 2)
    output = True
    for b in questions:
        if not b:
            output = False
            break
    return output


def For(*questions: bool):
    warnings.warn('This function is deprecated, use any() instead', DeprecationWarning, 2)
    output = False
    for b in questions:
        if b:
            output = True
            break
    return output


def switch_For(variable, *values):
    warnings.warn('This function is deprecated', DeprecationWarning, 2)
    return variable in values


def str_to_bool_soft(input: stb, return_false: bool = False):
    try:
        return str_to_bool(input)
    except TypeError:
        return False if return_false else input


def for_in(variable, mode: Literal['in', '==', 'is'], *values) -> bool:
    if mode == 'in':
        for value in values:
            if value in variable:
                return True
    elif mode == 'is':
        for value in values:
            if value is variable:
                return True
    else:
        for value in values:
            if value == variable:
                return True
    return False


def equals_all(*args) -> bool:
    args = list(args)
    first = args.pop(0)
    for arg in args:
        if first != arg:
            return False
    return True


def any(*args):
    return _any(args)


def all(*args):
    return _all(args)
