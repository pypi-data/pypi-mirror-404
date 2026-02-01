import string, re
from typing import Union
from random import randint, choice as randchoice
from hrenpack.listwork import split_list, ab_reverse, tuplist, _is_tuple

PYTHONNAME_LETTERS = string.ascii_lowercase + string.digits + '_'


def tuple_to_str(*args, letter: str = ',') -> str:
    output = ''
    for arg in args:
        if output == '':
            output = arg
        else:
            output = f'{output}{letter} {arg}'
    return output


def antienter_str(string: str, space: bool = True) -> str:
    string_list = string.split('\n')
    output = ''
    if space:
        for s in string_list:
            output = f'{output} {s}'
    else:
        for s in string_list:
            output = output + s
    return output


def zap_list(string: str, letter: str = ',', is_tuple: bool = False) -> list:
    output = string.split(letter)
    return tuple(output) if is_tuple else output


def antispace(string: str) -> str:
    space_list = string.split()
    output = ''
    for el in space_list:
        output = output + el
    return output


def string_add(*args: str) -> str:
    output = ''
    for s in args:
        output = output + s
    return output


def list_to_str(input: Union[list, tuple], separator: str = '') -> str:
    output = ''
    for element in input:
        output = f'{output}{separator}{element}'
    return output


def if_empty_str(string: str, empty: str, not_empty: str) -> str:
    return empty if string == '' else not_empty


def randstr(a: int, b: int) -> str:
    return str(randint(a, b))


def is_first(text: str, fragment: str) -> bool:
    if fragment not in text:
        return False
    else:
        length = fragment.__len__()
        return text[:length] == fragment


def is_last(text: str, fragment: str) -> bool:
    if fragment not in text:
        return False
    else:
        length = fragment.__len__()
        return text[-length:] == fragment


def search_and_edit(text: str, input: str, output: str) -> str:
    if input in text:
        frags = text.split(input)
        if frags.__len__() == 1:
            fragment = frags[0]
            if is_first(text, input):
                new_text = output + fragment
            elif is_last(text, input):
                new_text = fragment + output
            else:
                new_text = fragment
        else:
            new_text = split_list(frags, output)
            if is_first(text, input):
                new_text = output + new_text
            elif is_last(text, input):
                new_text = new_text + output
        return new_text
    else:
        return text


enter_fix = lambda text: search_and_edit(text, '\\n', '\n')


def prefix(base: str, prefix: str, is_suffix: bool = False) -> str:
    return '{} {}'.format(*ab_reverse(base, prefix, is_suffix, True))


def in_or(string: str, *args: str) -> bool:
    output = list()
    for arg in args:
        output.append(arg in string)
    return any(output)


def in_and(string: str, *args: str) -> bool:
    output = list()
    for arg in args:
        output.append(arg in string)
    return all(output)


def index_edit(string: str, index: int, letter: str) -> str:
    if len(letter) != 1:
        raise ValueError('Letter must be a single character')
    p1 = string[:index]
    p2 = string[index + 1:]
    return p1 + letter + p2


def string_reverse(string: str):
    output = list(string)
    output.reverse()
    return ''.join(output)


def index_edit_multi(string: str, values: dict[int, str]) -> str:
    for key, value in values.items():
        string = index_edit(string, key, value)
    return string


def index_edit_join(string: str, indexes: tuplist, values: Union[tuplist, str]) -> str:
    if len(indexes) != len(values):
        raise ValueError('Length of indexes must be equal to length of values')
    elif len(indexes) == 0 or len(values) == 0:
        raise ValueError('Empty indexes or values')
    else:
        for i in range(len(indexes)):
            if type(indexes[i]) is not int:
                raise ValueError('Indexes must be integers')
            if type(values[i]) is not str:
                raise ValueError('Values must be strings')
            string = index_edit(string, indexes[i], values[i])
        return string


def generate_rand_string(length: int = 25):
    return ''.join(randchoice(string.ascii_letters + string.digits) for _ in range(length))


def unspace(input: str):
    return input.replace(' ', '')


def unspace_multi(*strs: str) -> tuple:
    return tuple(unspace(s) for s in strs)


def remove_extra_spaces(text):
    # Заменяем несколько пробелов подряд на один
    return re.sub(r'\s+', ' ', text).strip()


def words_to_letters(*words: str, is_tuple: bool) -> tuplist:
    return _is_tuple(tuple(''.join(words)), is_tuple)


def only_this_letters(text: str, *letters: str) -> bool:
    letters = words_to_letters(*letters)
    for letter in text:
        if letter not in letters:
            return False
    return True


def only_pythonname(text: str) -> bool:
    return only_this_letters(text, PYTHONNAME_LETTERS)
