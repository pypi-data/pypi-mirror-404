import encodings, chardet
from typing import Union, Optional
from charset_normalizer import from_bytes
from hrenpack.listwork import replace_fragment_from_args

ALL_ENCODINGS = set(replace_fragment_from_args('_', '-', *set(encodings.aliases.aliases.values())))


def test_file_encoding(path: str, encoding: str, message: bool = False):
    try:
        with open(path, encoding=encoding) as file:
            try:
                file.read()
            except Exception as err:
                if message:
                    return f"Ошибка {err.__class__.__name__} в кодировке", encoding
                return False
            else:
                if message:
                    return "С кодировкой", encoding, "все нормально"
                return True
    except Exception as error:
        if message:
            return f"Ошибка {error.__class__.__name__} с открытием файла с кодировкой", encoding
        return False


def select_encoding(path: str) -> str:
    for enc in ALL_ENCODINGS:
        if test_file_encoding(path, enc):
            return enc


def test_all_encodings(path: str):
    for enc in ALL_ENCODINGS:
        print(test_file_encoding(path, enc, True))


def get_encoding(input: Union[str, bytes, bytearray]) -> str:
    return from_bytes(input).best().encoding


def convert_to_utf_8(input: bytes, encoding: Optional[str] = None) -> bytes:
    if encoding is None:
        encoding = get_encoding(input)
    return input.decode(encoding).encode('utf-8')


def detect_encoding(file_content):
    # Сначала проверяем явные маркеры (BOM)
    if file_content.startswith(b'\xef\xbb\xbf'):
        return 'utf-8-sig'
    elif file_content.startswith(b'\xff\xfe'):
        return 'utf-16'

    # Используем chardet для сложных случаев
    result = chardet.detect(file_content)
    encoding = result['encoding'].lower()

    # Корректируем типичные ошибки
    encoding_map = {
        'windows-1251': 'cp1251',
        'utf_8': 'utf-8',
        'ascii': 'utf-8'  # ASCII - подмножество UTF-8
    }
    return encoding_map.get(encoding, encoding)
