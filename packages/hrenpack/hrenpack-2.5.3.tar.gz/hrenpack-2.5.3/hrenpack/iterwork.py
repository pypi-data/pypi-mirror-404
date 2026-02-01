from typing import Iterable, Literal


def multi_in(input: Iterable, *args, condition: Literal['or', 'and'] = 'or'):
    if not args:
        raise ValueError('Must provide at least one argument')
    for arg in args:
        if arg not in input and condition == 'and':
            return False
        elif arg in input and condition == 'or':
            return True
    return True
