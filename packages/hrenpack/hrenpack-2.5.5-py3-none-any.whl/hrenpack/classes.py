import platform
from typing import Union, Optional, Iterable, Any
from types import MethodType
from dataclasses import dataclass
from hrenpack.decorators import args_kwargs
from hrenpack.listwork import split_list, intlist, floatlist, merging_dictionaries, if_dict_key, dict_keyf
from hrenpack.numwork import dec_to_hex, hex_to_dec


class stl(list):
    def __init__(self, source: Union[str, int, float, bool], *args, **kwargs) -> None:
        super().__init__()
        self.vstring = str(source)
        self.vlist = self.vstring.split(', ')
        self.save()
        self.__float__ = lambda: floatlist(self.vlist)
        self.__int__ = lambda: intlist(self.vlist)
        self.args, self.kwargs = args, kwargs
        self.not_empty = self.__bool__

    def __str__(self) -> str:
        return self.vstring

    def __list__(self) -> list:
        return self.vlist

    def __tuple__(self) -> tuple:
        return self.vtuple

    def save(self) -> None:
        self.vtuple = tuple(self.vlist)
        self.vstring = split_list(self.vlist)

    def split(self, isTuple: bool) -> Union[tuple, list]:
        return self.__tuple__() if isTuple else self.__list__()

    def append(self, value) -> None:
        self.vstring = f'{self.vstring}, {value}'
        self.vlist.append(value)
        self.save()

    def pop(self, index: int = -1) -> None:
        self.vlist.pop(index)
        self.save()

    def reverse(self) -> None:
        self.vlist.reverse()
        self.save()

    def remove(self, value) -> None:
        self.vlist.remove(value)
        self.save()

    def count(self, value) -> int:
        return self.vlist.count(value)

    def index(self, value, **kwargs) -> int:
        return self.vlist.index(value)

    def __len__(self) -> int:
        return len(self.vlist)

    def __bool__(self) -> bool:
        return bool(self.vlist)

    def __copy__(self):
        return stl(self.vstring)

    def __hash__(self):
        return hash(self.vstring)

    def __eq__(self, other) -> bool:
        return self.vstring == other.vstring

    def __ne__(self, other) -> bool:
        return self.vstring != other.vstring

    def clear(self):
        self.vlist.clear()
        self.save()

    def copy(self):
        return stl(self.vstring)

    def sort(self, *, key=None, reverse=False):
        self.vlist.sort(key=key, reverse=reverse)
        self.save()

    def __setitem__(self, key, value):
        self.vlist[key] = value
        self.save()

    def __getitem__(self, key):
        return self.vlist[key]

    def __delitem__(self, key):
        del self.vlist[key]
        self.save()

    def insert(self, __index, __object):
        self.vlist.insert(__index, __object)
        self.save()


class DictionaryWithExtendedFunctionality(dict):
    def __init__(self, **kwargs):
        super().__init__()
        self.__dict__ = kwargs

    def merge(self, *dicts):
        self.__dict__ = merging_dictionaries(self.__dict__, *dicts)


class MatrixCore:
    def __init__(self, path_to_file: str = '</return/>'):
        self.path_to_file = path_to_file
        self.is_return = self.path_to_file == '</return/>'

    class RectMatrix:
        def __init__(self, width: int, height: int, default_value=0):
            self.matrix = list()
            self.width, self.height = width, height
            for y in range(height):
                yl = list()
                for x in range(width):
                    yl.append(default_value)
                self.matrix.append(yl)

        def __setitem__(self, x: int, y: int, value):
            self.matrix[y][x] = value

        def __getitem__(self, x: int, y: int):
            return self.matrix[y][x]

        def __str__(self, separator: str = ' ') -> str:
            def step1(argument):
                def step2(arg):
                    def step3(a):
                        pass

                    vs = arg.split()
                    return split_list(vs, separator)

                al = argument.split('\n')
                al.pop(0)

                return split_list(al, '\n')

            output = ''
            for yl in self.matrix:
                po = ''
                for xel in yl:
                    po = po + separator + str(xel)
                output = output + '\n' + po
            return step1(output)


class DataClass:
    __default_classname__: str = 'DataClass'

    def __init__(self, **kwargs):
        self.__classname__ = kwargs.get('__classname__', self.__default_classname__)
        if '__classname__' in kwargs.keys():
            del kwargs['__classname__']
        self.__kwargs__: dict = kwargs
        self.__methods__ = ('__dict__', '__setitem__', '__getitem__', '__delitem__', '__len__', '__bool__', '__copy__',
                            '__update__', '__str__', '__clear__', '__methods__')
        self.__update__(**kwargs)

    def __dict__(self):
        return self.__kwargs__

    def __setitem__(self, key, value):
        self.__kwargs__[key] = value

    def __getitem__(self, key):
        return self.__kwargs__[key]

    def __delitem__(self, key):
        del self.__kwargs__[key]

    def __len__(self):
        return len(self.__kwargs__)

    def __bool__(self):
        return bool(self.__kwargs__)

    def __copy__(self):
        return DataClass(**self.kwargs)

    def __update__(self, **kwargs):
        for key, value in kwargs.items():
            if key not in self.__methods__:
                self.__kwargs__[key] = value
                setattr(self, key, value)
            else:
                raise ValueError(f"Имя {key} зарезервировано")

    # def __str__(self):
    #     classname = self.__classname__
    #     if classname == '</empty/>':
    #         string = ''
    #     else:
    #         string = classname + '('
    #     for key, value in self.__kwargs__.items():
    #         string += f'{key}={value}, '
    #     string = string[:-2]
    #     if classname != '</empty/>':
    #         string += ')'
    #     return string

    def __str__(self):
        string = self.__classname__ + '('
        for key, value in self.__kwargs__.items():
            string += f'{key}={value if type(value) is not str else f"'{value}'"}, '
        string = string[:-2]
        string += ')'
        return string

    def __clear__(self):
        self.__kwargs__.clear()

    def __ad_to_dt__(self):
        dicts = dict()
        for key, value in self.__kwargs__.items():
            if type(value) is dict:
                dicts[key] = PreEmptyDataClass(**value)
        self.__update__(**dicts)

    def __iter__(self):
        return iter(self.__kwargs__.items())


class PreEmptyDataClass(DataClass):
    __default_classname__ = ''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.__classname__ != self.__default_classname__:
            self.__update__(__classname__=self.__classname__)


class EmptyDataClass(DataClass):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            del self.__classname__, self.__default_classname__
        except AttributeError:
            pass

    def __str__(self):
        string = ''
        for key, value in self.__kwargs__.items():
            string += f'{key}={value}, '
        string = string[:-2]
        return string


def dicts_to_dataclasses(cls):
    if issubclass(cls, DataClass):
        init = cls.__init__

        def new_init(self, **kwargs):
            init(self, **kwargs)
            self.__ad_to_dt__()

        cls.__init__ = new_init
    else:
        raise TypeError("Задекорированный класс должен наследоваться от класса DataClass")


def call_method(method_name: str, objects: tuple, *args, **kwargs):
    for obj in objects:
        getattr(obj, method_name)(*args, **kwargs)


if platform.system() == 'Windows':
    from tkinter import *

    class TkTemplate(Tk):
        def __init__(self, title: str, width: int, height: int, background: str = 'white', resizable: bool = False, **kwargs):
            super().__init__()
            self.title(title)
            self.resizable(resizable, resizable)
            self.geometry(f'{width}x{height}')
            self['bg'] = background
            if if_dict_key(kwargs, 'icon'):
                self.iconbitmap(kwargs['icon'])
            self.stylesheet = dict_keyf(kwargs, 'stylesheet', dict())
            self.__stylesheet__()
            self.widgets_init()

        def widgets_init(self):
            pass

        def __stylesheet__(self):
            self.stylesheet_class = DataClass(**self.stylesheet)
else:
    class TkTemplate:
        def __new__(cls, *args, **kwargs):
            raise OSError('This class is only supported on Windows')

        def __init__(self, *args, **kwargs):
            raise OSError('This class is only supported on Windows')


class Color:
    def __init__(self, red: int, green: int, blue: int) -> None:
        self.red, self.green, self.blue = red, green, blue
        self.hexCode = self.__hex__()

    def __hex__(self) -> str:
        return '#' + dec_to_hex(self.red) + dec_to_hex(self.green) + dec_to_hex(self.blue)

    def __dict__(self) -> dict:
        return {'red': self.red, 'green': self.green, 'blue': self.blue, 'hex': self.hexCode}

    def shuffle(self, hexCode: str) -> None:
        self.red = (self.red + hex_to_dec(hexCode[1:3])) // 2
        self.green = (self.green + hex_to_dec(hexCode[3:5])) // 2
        self.blue = (self.blue + hex_to_dec(hexCode[5:7])) // 2
        self.hexCode = self.__hex__()


class Class:
    """Обычный пустой класс"""


class range_plus:
    def __init__(self, *args, **kwargs):
        if kwargs:
            new_args = (kwargs.get('start', 1), kwargs['end'], kwargs.get('step', 1))
        elif args:
            args = list(args)
            largs = len(args)
            if largs == 1:
                new_args = (1, args[0] + 1, 1)
            else:
                args[1] += 1
                if largs == 2:
                    new_args = (args[0], args[1], 1)
                elif largs == 3:
                    new_args = args
                else:
                    raise ValueError("Максимум 3 аргумента")
        else:
            raise ValueError("Нужен хотя бы 1 аргумент")
        self.range = range(*new_args)

    def __iter__(self):
        return iter(self.range)

    def __str__(self):
        return str(self.range)


def emptydataclass(cls):
    def str__(self):
        return super(type(self), self).__str__().replace(self.__class__.__name__, '', 1)
    cls = dataclass(cls)
    cls.__str__ = str__
    return cls


class RawString(str):
    def __add__(self, other):
        if not isinstance(other, str):
            other = str(other)
        return RawString(super().__add__(other))

    def __radd__(self, other):
        return RawString(str(other) + str(self))  # Гарантированно работает для любых типов

    def convert(self):
        return str(self)

    def __eq__(self, other):
        return other == self or str(other) == str(self)


class NoneType:
    def __bool__(self):
        return False

    def __int__(self):
        return 0

    def __float__(self):
        return 0.0

    def __str__(self):
        return ''

    def __eq__(self, other):
        return other is None or other == self

    def __ne__(self, other):
        return not self.__eq__(other)


class frozendict(dict):
    def __setitem__(self, key, value):
        raise TypeError(f"'{self.__class__.__name__}' object does not support item assignment")

    def __delitem__(self, key):
        raise TypeError(f"'{self.__class__.__name__}' object does not support item deletion")


class TransposedList:
    def __init__(self, data):
        """
        Инициализирует объект с данными для транспонирования.

        Args:
            data: Итерируемый объект с вложенными итерируемыми объектами одинаковой длины
        """
        self._validate_data(data)
        self._data = data

    def _validate_data(self, data):
        """Проверяет, что данные можно транспонировать."""
        try:
            iter(data)  # Проверяем, что объект итерируемый
            if not data:
                return  # Пустые данные допустимы

            # Проверяем, что все вложенные элементы имеют одинаковую длину
            first_len = len(data[0]) if hasattr(data[0], '__len__') else len(list(data[0]))
            for item in data:
                current_len = len(item) if hasattr(item, '__len__') else len(list(item))
                if current_len != first_len:
                    raise ValueError("All sub-iterables must have the same length")
        except TypeError as e:
            raise TypeError("Input data must be iterable") from e
        except IndexError as e:
            raise ValueError("Input data cannot be empty") from e

    def raw(self):
        """Возвращает исходные данные в виде списка."""
        return list(self._data) if not hasattr(self._data, '__len__') else self._data

    def __len__(self):
        """Возвращает количество строк в транспонированном представлении."""
        if not self._data:
            return 0
        first_item = self._data[0]
        return len(first_item) if hasattr(first_item, '__len__') else len(list(first_item))

    def __iter__(self):
        """Возвращает итератор по транспонированным данным."""
        # Если данные пустые, возвращаем пустой итератор
        if not self._data:
            return iter([])

        # Создаем итераторы для всех вложенных последовательностей
        iterators = [iter(subseq) for subseq in self._data]

        # Генерируем транспонированные строки
        while True:
            try:
                # Собираем элементы из каждого итератора
                yield [next(it) for it in iterators]
            except StopIteration:
                break

    def __getitem__(self, index):
        """Возвращает транспонированную строку по индексу."""
        try:
            # Проверяем, что индекс допустим
            if not isinstance(index, (int, slice)):
                raise TypeError("Index must be integer or slice")

            # Если данные пустые, вызываем исключение
            if not self._data:
                raise IndexError("Index out of range")

            # Получаем длину первой подпоследовательности
            first_len = len(self._data[0]) if hasattr(self._data[0], '__len__') else len(list(self._data[0]))

            # Обработка целочисленного индекса
            if isinstance(index, int):
                if index < -first_len or index >= first_len:
                    raise IndexError("Index out of range")

                # Возвращаем транспонированную строку
                return [subseq[index] if hasattr(subseq, '__getitem__') else list(subseq)[index]
                        for subseq in self._data]

            # Обработка слайса
            else:
                # Преобразуем в список, чтобы можно было делать несколько итераций
                data_list = list(self._data)
                # Получаем транспонированный список
                transposed = list(zip(*data_list))
                # Применяем слайс
                sliced = transposed[index]
                # Преобразуем обратно в список списков (а не кортежей)
                return [list(row) for row in sliced]

        except (IndexError, TypeError) as e:
            raise type(e)(f"Failed to get item at index {index}: {str(e)}") from e

    def __setitem__(self, index, value):
        """Устанавливает значение в транспонированной позиции."""
        try:
            # Проверяем, что индекс допустим
            if not isinstance(index, int):
                raise TypeError("Index must be integer for assignment")

            # Проверяем, что данные не пустые
            if not self._data:
                raise IndexError("Cannot assign to empty transposed sequence")

            # Проверяем, что значение имеет правильную длину
            if len(value) != len(self._data):
                raise ValueError(f"Value must have length {len(self._data)}")

            # Устанавливаем значения в исходные последовательности
            for i, subseq in enumerate(self._data):
                # Проверяем, поддерживает ли подпоследовательность присваивание
                if hasattr(subseq, '__setitem__'):
                    subseq[index] = value[i]
                else:
                    raise TypeError(f"Subsequence at position {i} does not support item assignment")

        except (IndexError, TypeError, ValueError) as e:
            raise type(e)(f"Failed to set item at index {index}: {str(e)}") from e

    def __delitem__(self, index):
        """Удаляет транспонированную строку по индексу."""
        try:
            # Проверяем, что индекс допустим
            if not isinstance(index, int):
                raise TypeError("Index must be integer for deletion")

            # Проверяем, что данные не пустые
            if not self._data:
                raise IndexError("Cannot delete from empty transposed sequence")

            # Удаляем элементы из исходных последовательностей
            for subseq in self._data:
                # Проверяем, поддерживает ли подпоследовательность удаление
                if hasattr(subseq, '__delitem__'):
                    del subseq[index]
                else:
                    raise TypeError("Subsequence does not support item deletion")

        except (IndexError, TypeError) as e:
            raise type(e)(f"Failed to delete item at index {index}: {str(e)}") from e

    def __repr__(self):
        """Строковое представление объекта."""
        return f"TransposedList({self._data})"

    def __str__(self):
        """Строковое представление транспонированных данных."""
        transposed = list(self)
        return str(transposed)


class TupleDict:
    def __init__(self, *args: tuple[Any, Any]):
        self._data = list(args)

    def to_dict(self) -> dict:
        output = dict()
        for key, value in self._data:
            output[key] = value
        return output

    def __iter__(self):
        return iter(self.to_dict())

    def __getitem__(self, index):
        return self.to_dict()[index]

    def __setitem__(self, index, value):
        self.to_dict()[index] = value

    def __delitem__(self, index):
        del self.to_dict()[index]
