import os, json, csv
from typing import Union, Literal, Any, List
from hrenpack import one_return
from hrenpack.cmd import get_filename, get_extension, create_file, delete_file, FileNameInfo
from hrenpack.listwork import (split_list, _is_tuple, list_add, split_list_enter, split_list_space, key_in_dict,
                               equals_keys)
from hrenpack.strwork import search_and_edit
from hrenpack.decorators import confirm
from configparser import ConfigParser


class FileTypeError(Exception):
    pass


class FileIsNotEmptyError(Exception):
    pass


class FileIsEmptyError(Exception):
    pass


def extension_check(path: str, *extensions: Union[list, tuple, str]) -> None:
    extensions_converted = list()
    for e in extensions:
        if type(e) is str:
            extensions_converted.append(e)
        else:
            for g in e:
                extensions_converted.append(g)

    extension = get_extension(path)
    if extension not in extensions_converted:
        raise FileTypeError(f"Данный класс предназначен для {split_list(extensions)} файлов. "
                            f"Ваш файл с расширением {extension}")


def create_file_if_not_exists(path: Union[str, FileNameInfo]) -> None:
    path = path if type(path) is str else path.path
    if not os.path.isfile(path):
        create_file(path)


class TextFile:
    comment_letter = ''

    def __init__(self, path: Union[str, FileNameInfo], encoding: Union[str, int] = 'utf-8', **kwargs):
        self.path = path if type(path) is str else path.path
        self.get_filename = lambda: get_filename(self.path)
        self.get_extension = lambda: get_extension(self.path)
        self.encoding = str(encoding)
        self.search_and_delete = lambda input: self.search_and_edit(input, '')
        self._comments = list()
        if key_in_dict(kwargs, 'extension'):
            extension_check(path, kwargs['extension'])
        elif key_in_dict(kwargs, 'extensions'):
            extension_check(path, *kwargs['extensions'])
        create_file_if_not_exists(self.path)

    @staticmethod
    def comment_decorator(func):
        def wrapper(self, *args, **kwargs):
            if self.comment_letter == '':
                raise AttributeError(
                    f"AttributeError: '{self.__class__.__name__}' object has no attribute 'add_comment'")
            return func(self, *args, **kwargs)
        return wrapper

    def read(self, letters: int = -1) -> str:
        file = open(self.path, encoding=self.encoding)
        data = file.read(letters)
        file.close()
        return data

    def rewrite(self, data: str):
        file = open(self.path, 'w', encoding=self.encoding)
        file.write(data)
        file.close()

    def add_data(self, data: str, separator: str = ''):
        file = open(self.path, 'a', encoding=self.encoding)
        file.write(separator)
        file.write(data)
        file.close()

    @comment_decorator
    def add_comment(self, comment: str):
        if '\n' in comment:
            raise ValueError('\\n in comment')
        self.add_data('{} {}'.format(self.comment_letter, comment))

    def copy(self, new_path: str):
        if not os.path.isfile(new_path):
            raise FileExistsError(
                f'[WinError 183] Невозможно создать новый файл, так как он уже существует: {new_path}'
            )
        else:
            data = self.read()
            file = open(new_path, 'w', encoding=self.encoding)
            file.write(data)
            file.close()

    def copy_and_edit_text(self, new_path: str, new_text: str):
        self.copy(new_path)
        file = TextFile(new_path)
        file.rewrite(new_text)

    def copy_with_prefix(self, prefix_text: str, is_suffix: bool = False,
                         new_text: Union[str, bool] = False, is_return_filename: bool = False) -> str:
        if is_suffix:
            new_filename = f'{self.path} {prefix_text}'
        else:
            new_filename = f'{prefix_text} {self.path}'

        self.copy(new_filename)

        if new_text is not False:
            copyed_file = TextFile(new_filename)
            copyed_file.rewrite(new_text)

        if is_return_filename:
            return new_filename

    # Номер строки (line) считается начиная с единицы
    def edit_line(self, line: int, new_data: str):
        lines = self.read().split('\n')
        lines[line - 1] = new_data
        self.rewrite(split_list(lines, '\n'))

    def is_empty(self) -> bool:
        return self.read() == ''

    def search_and_edit(self, input: str, output: str) -> None:
        new_text = search_and_edit(self.read(), input, output)
        self.rewrite(new_text)

    def write_if_is_empty(self, data):
        if self.is_empty():
            self.rewrite(data)
        else:
            raise FileIsNotEmptyError("Для использования этой функции файл должен быть пустым")

    def read_lines(self, is_tuple: bool = False, without_n: bool = True) -> Union[list[str], tuple[str]]:
        output = self.read().split('\n')
        if not without_n:
            for el in output:
                el += '\n'
        return _is_tuple(output, is_tuple)

    def __copy__(self, new_path: str):
        self.copy(new_path)
        return TextFile(new_path)

    @confirm("Данное действие удалит файл. Вы уверены, что хотите продолжить?")
    def delete(self):
        delete_file(self.path)
        del self

    def newline(self, line: str):
        if self.is_empty():
            self.rewrite(line)
        else:
            self.rewrite(f'{self.read()}\n{line}')

    def __str__(self):
        return self.read()

    def __bool__(self):
        return self.is_empty()

    def open(self,
             mode: Literal[
                 "r+", "+r", "rt+", "r+t", "+rt", "tr+", "t+r", "+tr", "w+", "+w", "wt+", "w+t", "+wt", "tw+", "t+w", "+tw", "a+", "+a", "at+", "a+t", "+at", "ta+", "t+a", "+ta", "x+", "+x", "xt+", "x+t", "+xt", "tx+", "t+x", "+tx", "w", "wt", "tw", "a", "at", "ta", "x", "xt", "tx", "r", "rt", "tr", "U", "rU", "Ur", "rtU", "rUt", "Urt", "trU", "tUr", "Utr"] = "r",
             buffering: int = -1,
             errors: str | None = None,
             newline: str | None = None,
             closefd: bool = True):
        return open(self.path, mode, buffering, self.encoding, errors, newline, closefd)


# Важно! Для использования класса файл SRT должен быть написан по всем правилам (между разными типами данных должен быть
# один переход на новую строку, между секциями должно быть два перехода на новую строку)
class SRTSubtitleFile(TextFile):
    class SubtitleError(Exception):
        pass

    def __init__(self, path: str, encoding: Union[str, int] = 'utf-8'):
        super().__init__(path, encoding)
        extension_check(path, 'srt')
        self.subtitles_timecodes = self.read_subtitle()['timecodes']
        self.subtitles_text = self.read_subtitle()['text']
        self.sections = self.read_subtitle()['number']
        self.edit, self.elst, self.edit_subtitle = one_return(3, self.edit_line_subtitle_text)

    def read_subtitle(self) -> dict:
        try:
            sections = self.read().split('\n\n')
            timecodes, text_data = one_return(2, list())
            for section in sections:
                number, timecode, text = section.split('\n')
                timecodes.append(timecode)
                text_data.append(text)
            return {'timecodes': timecodes, 'text': text_data, 'number': len(sections)}
        except ValueError:
            if not self.is_empty():
                raise self.SubtitleError("Данный файл субтитров построен неправильно. Наша библиотека не может с ним"
                                         " работать. Приносим извинения за предоставленные неудобства.")

    def edit_line_subtitle_text(self, line: int, new_text: str):
        text_line = line * 4 - 1
        self.edit_line(text_line, new_text)

    def edit_timecode(self, line: int, new_timecode_begin: str, new_timecode_end: str):
        text_line = line * 4 - 2
        self.edit_line(text_line, f'{new_timecode_begin} --> {new_timecode_end}')


class ConfigurationFile(TextFile):
    comment_letter = ';'

    class Converter:
        def __init__(self, config: ConfigParser, get_value):
            self.config = config
            self.get_value = get_value

        def __bool__(self, section: str, key: str) -> bool:
            return self.config.getboolean(section, key)

        def __int__(self, section: str, key: str) -> int:
            return self.config.getint(section, key)

        def __float__(self, section: str, key: str) -> float:
            return self.config.getfloat(section, key)

        def convert_enter(self, section: str, key: str) -> str:
            value = self.get_value(section, key)
            return search_and_edit(value, '\\n', '\n')

    def __init__(self, path: str = 'config.ini', encoding: Union[str, int] = 'utf-8'):
        super().__init__(path, encoding)
        extension_check(self.path, 'ini')
        self.config = ConfigParser()
        self.read_config = lambda: self.config.read(self.path, encoding=self.encoding)
        self.read_config()
        self.convert = self.Converter(self.config, self.get_value)
        self.get_bool = self.get_boolean

    def get_value(self, section: str, key: str) -> str:
        return self.config.get(section, key)

    def get_boolean(self, section: str, key: str) -> bool:
        return self.config.getboolean(section, key)

    def get_int(self, section: str, key: str) -> int:
        return self.config.getint(section, key)

    def get_float(self, section: str, key: str) -> float:
        return self.config.getfloat(section, key)

    def set_value(self, section: str, key: str, value) -> None:
        self.config.set(section, key, str(value))
        self.save()

    def save(self):
        with open(self.path, 'w', encoding=self.encoding) as config:
            self.config.write(config)

    def section_exists(self, section: str) -> bool:
        return section in self.config.sections()

    def value_exists(self, section: str, key: str) -> bool:
        return self.config.has_option(section, key)

    def delete_value(self, section: str, key: str) -> None:
        self.config.delete(section, key)
        self.save()

    def delete_section(self, section: str) -> None:
        self.config.delete(section)
        self.save()

    def create_section(self, section: str) -> None:
        self.config.add_section(section)
        self.save()

    def create_key_in_section(self, section: str, key: str, value) -> None:
        if not self.value_exists(section, key):
            if not self.section_exists(section):
                self.create_section(section)
                self.config.set(section, key, str(value))
                self.save()
            else:
                self.config.set(section, key, str(value))
                self.save()
        else:
            if not value == self.get_value(section, key):
                self.set_value(section, key, str(value))

    def add_comment(self, line_index: int, text: str, comment_letter: Literal[';', '#'] = ';'):
        lines = self.read_lines()
        lines = list_add(lines, line_index, split_list_space((comment_letter, text)))
        self.rewrite(split_list_enter(lines))

    def edit_section(self, section: str, block: dict, rewrite: bool = False) -> None:
        if rewrite:
            self.delete_section(section)
            self.create_section(section)
        for key in block:
            self.set_value(section, key, block[key])

    def rewrite(self, data: str):
        with open(self.path, 'w', encoding=self.encoding) as file:
            file.write(data)
            self.read_config()

    def set_bool(self, section: str, key: str, value):
        self.set_value(section, key, bool(value))

    def set_int(self, section: str, key: str, value):
        self.set_value(section, key, int(value))

    def get_section(self, section: str, is_dict: bool = True) -> Union[list[tuple[str, str]], dict]:
        output = self.config.items(section)
        if is_dict:
            pre_output = dict()
            for el in output:
                pre_output[el[0]] = el[1]
            output = pre_output
        return output

    def edit(self, block: dict[str, dict[str, Any]], rewrite: bool = False) -> None:
        if rewrite:
            config = ConfigParser()
            for section, options in block.items():
                config[section] = options
            with open('output.ini', 'w') as configfile:
                config.write(configfile)
        else:
            for section, options in block.items():
                self.edit_section(section, options)

    def edit_section_if_not_none(self, section: str, block: dict, rewrite: bool = False) -> None:
        output = dict()
        for key, value in block.items():
            if value not in (None, 'None'):
                output[key] = value
        self.edit_section(section, output, rewrite)

    def edit_if_not_none(self, block: dict[str, dict[str, Any]], rewrite: bool = False) -> None:
        for section, options in block.items():
            self.edit_section_if_not_none(section, options, rewrite)


class JavaScriptObjectNotationFile(TextFile):
    class JSONError(Exception):
        pass

    def __init__(self, path: str, encoding: Union[str, int] = 'utf-8'):
        super().__init__(path, encoding)
        extension_check(self.path, 'json')
        self.data = json.loads(self.read())

    def __dict__(self):
        return self.data

    def __len__(self):
        return len(self.data)

    def __bool__(self):
        return bool(self.data)

    def save(self):
        with open(self.path, 'w', encoding=self.encoding) as file:
            json.dump(self.data, file, indent=4, ensure_ascii=self.encoding.islower() == 'ascii')

    def get_value(self, key, default=KeyError()):
        try:
            if type(default) is KeyError:
                raise default
            return self.data.get(key, default)
        except KeyError:
            raise self.JSONError(f"В файле {get_filename(self.path)} не существует ключа {key}")

    def set_value(self, key, value):
        self.data[key] = value
        self.save()

    def delete_value(self, key):
        del self.data[key]
        self.save()

    def __setitem__(self, key, value):
        self.data[key] = value
        self.save()

    def __getitem__(self, key):
        return self.data[key]

    def __delitem__(self, key):
        del self.data[key]
        self.save()

    def __iter__(self):
        return iter(self.data)

    def set_values(self, **values):
        for key, value in values.items():
            self.data[key] = value
        self.save()

    def get_values(self, *keys):
        output = dict()
        for key in keys:
            output[key] = self.get_value(key)
        return output

    def key_exists(self, key) -> bool:
        return key in self.data

    def add_dict(self, data: dict):
        self.set_values(**data)

    def clear(self):
        self.data.clear()
        self.save()

    def rewrite_dict(self, data: dict):
        self.clear()
        self.add_dict(data)

    def rewrite_values(self, **values):
        self.rewrite_dict(values)

    def __str__(self):
        return str(self.data)

    def read_data(self):
        return self.data


def write_file_if_not_exists(path: str, text: str = ''):
    if os.path.isfile(path):
        raise FileExistsError(f'[WinError 183] Невозможно создать новый файл, так как он уже существует: {path}')
    else:
        create_file(path)
        file = TextFile(path)
        file.rewrite(text)


class CommaSeparatedValuesFile(TextFile):
    def __init__(self, path: str, encoding: Union[str, int] = 'utf-8'):
        super().__init__(path, encoding)

    def read_data(self):
        with self.open() as file:
            return csv.DictReader(file)

    def write_data(self, data: List[dict[str, Any]]):
        with self.open('w', newline='') as file:
            fields = equals_keys(*data)
            if fields is None:
                raise ValueError
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            writer.writerows(data)

# class CascadeStyleSheetsFile(TextFile):
#     def __init__(self, path: str, encoding: Union[str, int] = 'utf-8'):
#         super().__init__(path, encoding)
#
#     def save(self):
#
