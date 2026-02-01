import mimetypes
from hrenpack.constants import MIME_TYPES, COMPOUND_EXTENSIONS


def get_mime_type(path: str):
    return mimetypes.guess_type(path)[0] or 'application/octet-stream'


def get_mime_type_extension(path: str):
    pass


def get_mime_type_filetype(path: str):
    from filetype import guess
    kind = guess(path)
    if kind is None:
        return 'application/octet-stream'
    return kind.mime


def get_mime_type_magic(path: str):
    from puremagic import from_file
    return from_file(path, True)


if __name__ == '__main__':
    print(get_mime_type('d.cpp'))
