import re
from typing import Union, Literal, Optional, Iterable
from hrenpack.boolwork import Fand

tuplist = Union[tuple, list]
tdl = Union[tuple, dict, list]


def _is_tuple(input: Iterable, is_tuple: bool) -> Union[tuple, list]:
    return tuple(input) if is_tuple else list(input)


def antizero(wnull):
    if wnull < 10:
        output = '0' + str(wnull)
    else:
        output = str(wnull)
    return output


def listsearch(list, search):
    for i in range(len(list)):
        if list[i] == search:
            index = i
            break
        else:
            index = False
    return index


def antienter(list):
    o = ''
    for i in range(len(list)):
        o = o + list[i]
    output = o.split('\n')
    return output


def antienter_plus(list):
    o = ''
    for i in range(len(list)):
        o = o + list[i]
    output = o.split('\n')
    el0 = output[0].split('\ufeff')
    pel = el0[-1]
    output[0] = pel
    output.pop()
    return output


def intlist(input: list) -> list:
    for i in range(len(input)):
        input[i] = int(input[i])
    return input


def floatlist(input: tuplist) -> list:
    input = list(input)
    for i in range(len(input)):
        input[i] = float(input[i])
    return input


def list_add(input: list, index: int, data) -> list:
    forcikl = len(input) + 1
    output = list()
    for i in range(forcikl):
        if i < index:
            output.append(input[i])
        elif i == index:
            output.append(data)
        elif i > index:
            m = i - 1
            output.append(input[m])
    return output


def str_to_list_one(string: str) -> list:
    output = list()
    for letter in string:
        output.append(letter)
    return output


def in_number_series(ot: int, to: int, num: int) -> bool:
    number_series = list()
    for i in range(ot, to):
        number_series.append(i)
    return num in number_series


def in_numbers(ot: int, to: int, nums: Union[tuple, dict, list]) -> dict:
    is_dict = dict()
    for num in nums:
        is_dict[num] = in_number_series(ot, to, num)
    return is_dict


def dict_to_list(input: dict, is_tuple: bool):
    output = list()
    for key in input:
        value = input[key]
        output.append(value)
    return _is_tuple(output, is_tuple)


def multi_pop(input: list, *indexes: int):
    for i in range(len(indexes)):
        index = indexes[i] - i
        try:
            if index == len(input) - 1:
                input.pop()
            else:
                input.pop(index)
        except IndexError:
            pass
    return input


def if_dict_key(dct: dict, key):
    try:
        dct[key]
    except KeyError:
        return False
    else:
        return True


def split_list(input: Union[tuple, list], separator: str = ', '):
    return separator.join(input)


def merging_dictionaries(*dicts: dict) -> dict:
    output = dict()
    for d in dicts:
        output = {**output, **d}
    return output


# -1 - pseudo dict to dict
# 0 - выполнять в любом случае
# 1 - dict to pseudo dict
def pseudo_dictionary(input: tdl, not_edit_type: Literal[-1, 0, 1] = 0) -> tdl:
    if type(input) is dict and not_edit_type in (0, 1):
        output = list()
        for key, value in input.items():
            output.append((key, value))
    elif type(input) in (list, tuple) and not_edit_type in (-1, 0):
        output = dict()
        for el in input:
            key, value = el
            output[key] = value
    else:
        output = input
    return output


def variable_in_tuple(variable, *values):
    return variable in values


def pop(input: list, index: int = -1):
    input.pop(index)
    return input


split_list_enter = lambda input: split_list(input, '\n')
split_list_space = lambda input: split_list(input, ' ')
split_list_tab = lambda input: split_list(input, '\t')
dict_key_null = lambda dct, key: dct[key] if key in dct else None
dict_key_false = lambda dct, key: dct[key] if key in dct else False
dict_key_tf = lambda dct, key, true, false: true if key in dct else false
dict_keyf = lambda dct, key, false: dct[key] if key in dct else false
key_in_dict = lambda dct, key: dict_key_tf(dct, key, True, False)


def ab_reverse(a, b, condition: bool, is_tuple: bool = True) -> tuplist:
    output = [a, b]
    if condition:
        output.reverse()
    return tuple(output) if is_tuple else output


def ab_not_reverse(a, b, condition: bool, is_tuple: bool = True) -> tuplist:
    output = ab_reverse(a, b, condition, is_tuple)
    output.reverse()
    return output


def multi_reverse(condition, *args, is_tuple: bool = True) -> tuplist:
    args = list(args)
    if condition:
        args.reverse()
    return tuple(args) if is_tuple else args


def multi_not_reverse(condition, *args, is_tuple: bool = True) -> tuplist:
    output = multi_reverse(condition, *args, is_tuple=is_tuple)
    output.reverse()
    return output


def dict_keys_values(keys: tuplist, values: tuplist) -> dict:
    return dict(zip(keys, values))


def dkv_dict(source: dict, keys: tuplist, values: tuplist) -> dict:
    return merging_dictionaries(source, dict_keys_values(keys, values))


def remove_all(input: list, value, is_tuple: bool = False):
    count = input.count(value)
    for i in range(count):
        input.remove(value)
    return _is_tuple(input, is_tuple)


def remove_multi(input: list, *values, _remove_all: bool = False, is_tuple: bool = False):
    if _remove_all:
        for value in values:
            input = remove_all(input, value)
    else:
        for value in values:
            input.remove(value)
    return _is_tuple(input, is_tuple)


def list_to_list(input: list, index: Optional[int] = None, element=None, is_tuple: bool = True) -> tuplist:
    if index is not None and element is not None:
        raise TypeError("Оба аргумента не равняются None")
    elif index is None:
        index = input.index(element)
    in2 = input[index:-1]
    in2.pop(0)
    in2.append(input[-1])
    return _is_tuple((input[0:index], in2), is_tuple)


def list_tuple_to_str(input) -> str:
    try:
        if input is None:
            output = '()'
        elif isinstance(input, list) or Fand(isinstance(input, tuple), len(input) > 1):
            output = str(input)
        elif isinstance(input, tuple) and len(input) == 1:
            output = f'({input[0]})'
        else:
            output = f'({input})'
        return output
    except TypeError:
        return f'({input})'


def split_quotes(text: str, is_tuple: bool = False) -> tuplist:
    pattern = r"""
            (?:
                "(?:[^"\\]|\\.)*"
                |
                '(?:[^'\\]|\\.)*'
                |
                \S+              
            )
        """
    tokens = re.findall(pattern, text, re.VERBOSE)
    return _is_tuple(tokens, is_tuple)


def get_values_by_keys(input: dict, *keys, is_tuple: bool = False) -> tuplist:
    output = list()
    for key in keys:
        output.append(input[key])
    return _is_tuple(output, is_tuple)


def del_keys(input: dict, *keys) -> None:
    for key in keys:
        del input[key]


def dict_index(input: dict, value):
    for k, v in input.items():
        if v == value:
            return k
    else:
        raise ValueError(f"Словарь {input} не содержит значения {value}")


def strlist(input: tuplist, is_tuple: bool = False):
    input = list(input)
    for i in range(len(input)):
        input[i] = str(input[i])
    return _is_tuple(input, is_tuple)


def keys_dict_equals(*dicts: dict) -> bool:
    dicts = list(dicts)
    first = tuple(dicts.pop(0).keys())
    for d in dicts:
        if first != tuple(d.keys()):
            return False
    return True


def equals_keys(*dicts: dict) -> tuple:
    if keys_dict_equals(*dicts):
        return tuple(dicts[0].keys())


def del_none(*args, is_tuple: bool = False) -> tuplist:
    args = list(args)
    for i, arg in enumerate(args):
        if arg is None:
            args.pop(i)
    return _is_tuple(args, is_tuple)


def del_none_from_dict(*dicts, **kwargs) -> dict:
    kwargs = merging_dictionaries(*dicts, kwargs)
    output = kwargs.copy()
    for key, value in kwargs.items():
        if value is None:
            output.pop(key)
    return output


def enum_tuple(iterable):
    return enumerate(tuple(iterable))


def split_list_to_lists(input: tuplist, *indexes: int, is_tuple: bool = False,
                        in_start: bool = True, in_end: bool = False) -> list:
    input = list(input)
    output = list()
    for i in range(len(indexes)):
        cur = indexes[i]
        past = indexes[i - 1] if i > 0 else 0
        if not in_start and past > 0:
            past -= 1
        if in_end:
            cur += 1
        sl = input[:cur] if past == 0 else input[past:cur]
        output.append(sl)
    return _is_tuple(output, is_tuple)


def get_from_dict(input: dict, *keys, only_values: bool = False, is_tuple: bool = False, default=None,
                  pop_mode: bool = False) -> tdl:
    output = dict()
    for key in keys:
        value = input.pop(key, default)
        output[key] = value
        if not pop_mode:
            input[key] = value
    if only_values:
        return _is_tuple(output.values(), is_tuple)
    return output


def replace_fragment_from_args(old_frag: str, new_frag: str, *args: str, is_tuple: bool = False) -> tuplist:
    output = list()
    for arg in args:
        output.append(arg.replace(old_frag, new_frag))
    return _is_tuple(output, is_tuple)


class dict_enumerate:
    def __init__(self, items: dict):
        self.items = items.items() if isinstance(items, dict) else items

    def __iter__(self):
        output = list()
        for i, kv in enumerate(self.items):
            output.append((i, *kv))
        return iter(output)


def selective_slice(input, *keys, only_values: bool = False, is_tuple: bool = False) -> tdl:
    output = dict()
    for key in keys:
        output[key] = input[key]
    if only_values:
        return _is_tuple(output.values(), is_tuple)
    return output


def dict_get(dct: dict, key, default=None):
    output = dct.get(key)
    if output and output is not False:
        return default
    return output


def mislist(input: tuplist, *args, is_tuple: bool = False) -> tuplist:
    output = list()
    for arg in args:
        if arg not in input:
            output.append(arg)
    return _is_tuple(output, is_tuple)


def dict_slice(input: dict, *keys, only_values: bool = False, is_tuple: bool = False, all_required: bool = False) -> tdl:
    output = dict()
    for key in keys:
        if key in input:
            output[key] = input[key]
        elif all_required:
            raise KeyError(key)
    return _is_tuple(output.values(), is_tuple) if only_values else output
