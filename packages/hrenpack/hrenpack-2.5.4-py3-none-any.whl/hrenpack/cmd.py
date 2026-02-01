import os, ctypes, shutil, getpass, platform, random, string, subprocess, filetype, warnings
from datetime import datetime
from hrenpack.listwork import split_list
from typing import Union, List, Type
from dataclasses import dataclass
from pathlib import Path

PathType = Union[str, Path]


def get_filename(path: str, raise_error: bool = True) -> str:
    if '/' in path:
        output = path.split('/')[-1]
    elif '\\' in path:
        output = path.split('\\')[-1]
    else:
        output = path

    if not os.path.isfile(path) and raise_error:
        raise FileNotFoundError('No such file: ' + path)
    else:
        return output


def get_extension(path: str, raise_error: bool = True) -> str:
    filename = get_filename(path, raise_error)
    return filename.split('.')[-1] if '.' in filename else ''


def get_path_without_filename(path: str, raise_error: bool = True):
    v85 = True
    if '/' in path:
        path_list = path.split('/')
        path_list.pop()
    elif '\\' in path:
        path_list = path.split('\\')
        path_list.pop()
    else:
        v85 = False
    output = split_list(path_list, '/') if v85 else ''
    if not os.path.isfile(path) and raise_error:
        raise FileNotFoundError('No such file: ' + path)
    else:
        return output


def get_path_and_filename(path: str, raise_error: bool = True):
    if raise_error and not os.path.isfile(path):
        raise FileNotFoundError('No such file: ' + path)
    return get_path_without_filename(path), get_filename(path)


def rename(path: str, new_filename: str):
    pwfn, filename = get_path_and_filename(path)
    if pwfn:
        new_path = f'{pwfn}/{new_filename}'
    else:
        new_path = new_filename
    os.rename(path, new_path)


def create_file(path: str):
    try:
        open(path, 'x').close()
    except FileExistsError:
        raise FileExistsError(f'[WinError 183] Невозможно создать новый файл, так как он уже существует: {path}')


def get_filename_without_extension(path: str, raise_error: bool = True) -> str:
    filename = get_filename(path, raise_error)
    fl = filename.split('.')
    fl.pop()
    return split_list(fl, '.')


def get_path_without_extension(path: str, raise_error: bool = True) -> str:
    filename = get_filename_without_extension(path, raise_error)
    pwfl = get_path_without_filename(path, raise_error)
    return f'{pwfl}/{filename}'


@dataclass
class FileNameInfo:
    path: str
    filename: str = ''
    extension: str = ''
    path_without_extension: str = ''
    path_without_filename: str = ''

    def __post_init__(self):
        self.filename = get_filename(self.path)
        self.extension = get_extension(self.path)
        self.path_without_extension = get_path_without_filename(self.path)
        self.path_without_filename = get_path_without_extension(self.path)


def delete_file(path: str):
    os.remove(path)


def create_file_exist(path: str, space: bool = True, return_filename_and_path: bool = False):
    if not os.path.isfile(path):
        new_path = path
    else:
        counter = 0
        separator = ' ' if space else ''
        pafn = get_path_without_extension(path, False)
        extension = get_extension(path)
        while True:
            new_path = f'{pafn}{separator}({counter}).{extension}'
            if os.path.isfile(new_path):
                counter += 1
            else:
                break

    create_file(new_path)

    if return_filename_and_path:
        return FileNameInfo(new_path)
    return None


def edit_time(year: int = -1, month: int = -1, day: int = -1, hour: int = -1, minute: int = -1,
              second: int = -1) -> None:
    now = datetime.now()
    if year < 0:
        year = now.year
    if month < 0:
        month = now.month
    if day < 0:
        day = now.day
    if hour < 0:
        hour = now.hour
    if minute < 0:
        minute = now.minute
    if second < 0:
        second = now.second

    os.system(f'date {year}.{month}.{day}')
    os.system(f'time {hour}:{minute}:{second}')


def is_admin() -> bool:
    return bool(ctypes.windll.shell32.IsUserAnAdmin())


def admin_error() -> None:
    if not is_admin():
        raise OSError("Перезапустите программу с правами администратора")


def admin_pause() -> None:
    if not is_admin():
        print("Перезапустите программу с правами администратора")
        input()


def admin_pause_exit() -> None:
    admin_pause()
    exit(1)


def remove_files_and_folders(*paths):
    for path in paths:
        if os.path.isfile(path):
            try:
                os.remove(path)
            except Exception as e:
                raise OSError(f"Не удалось удалить файл {path}: {e}")
        elif os.path.isdir(path):
            try:
                shutil.rmtree(path)
            except Exception as e:
                raise OSError(f"Не удалось удалить папку {path}: {e}")


def get_username() -> str:
    return getpass.getuser()


def android_path(path: str, domain: str, name: str) -> str:
    if platform.system() == 'Windows':
        return path
    return f'data/data/{domain}.{name}/files/app/{path}'


class AndroidPath:
    def __init__(self, domain: str, name: str):
        self.domain = domain
        self.name = name

    def __call__(self, path: str) -> str:
        if platform.system() == 'Windows':
            return path
        return f'data/data/{self.domain}.{self.name}/files/app/{path}'


def get_files_startswith(directory: str, start: str, full_path: bool = True) -> List[str]:
    files = os.listdir(directory)
    filtered_files = [f for f in files if f.startswith(start)]
    if full_path:
        output = list()
        for file in filtered_files:
            output.append(os.path.join(directory, file))
    else:
        output = filtered_files
    return output


def all_files_and_dirs(directory):
    output = []
    for root, dirs, files in os.walk(directory):
        output.extend([os.path.join(root, name) for name in files])
        output.extend([os.path.join(root, name) for name in dirs])
    return output


def all_files(directory, full_path: bool = True) -> List[str]:
    path = Path(directory)
    if not full_path:
        return [get_filename(str(file)) for file in path.rglob('*') if file.is_file()]
    return [str(file) for file in path.rglob('*') if file.is_file()]


def generate_random_filename(length: int = 10, extension: str = '') -> str:
    letters_and_digits = string.ascii_letters + string.digits
    random_name = ''.join(random.choice(letters_and_digits) for _ in range(length))
    if extension:
        extension = '.' + extension
    return random_name + extension


def compare_versions(version1, version2):
    version1_parts = list(map(int, version1.split('.')))
    version2_parts = list(map(int, version2.split('.')))

    # Сравниваем по частям
    for v1, v2 in zip(version1_parts, version2_parts):
        if v1 > v2:
            return 1
        elif v1 < v2:
            return -1
    return 0


def uninstall_program(program_name):
    try:
        # Выполняем команду для деинсталляции программы
        subprocess.run(['wmic', 'product', 'where', f'name="{program_name}"', 'call', 'uninstall'], check=True)
        print(f'Программа "{program_name}" успешно деинсталлирована.')
    except subprocess.CalledProcessError as e:
        print(f'Ошибка при деинсталляции программы: {e}')


def get_mime_type(path: str):
    warnings.warn('This function has been moved to the filetype module', DeprecationWarning, 2)
    kind = filetype.guess(path)
    if kind is None:
        if get_extension(path) == 'txt':
            return 'text/plain'
        return 'text/' + get_extension(path)
    return kind.mime


def admin_required(func):
    def wrapper(*args, **kwargs):
        if is_admin():
            return func(*args, **kwargs)
        raise OSError("Отказано в доступе")
    return wrapper


def package_is_debug(file: Path, tree_level: int = 1):
    if not file.is_file() or not file.exists() or get_extension(str(file)) != 'py':
        raise FileNotFoundError
    for level in range(tree_level + 1):
        file = file.parent
    if not file.is_dir():
        raise NotADirectoryError
    return file.name != 'site-packages'


class PackageIsDebug:
    def __init__(self, file: Union[Path, str], tree_level: int = 1):
        file = file if isinstance(file, Path) else Path(file)
        if not file.is_file() or not file.exists() or get_extension(str(file)) != 'py':
            raise FileNotFoundError
        self.file = file
        self.tree_level = tree_level

    def get_directory(self):
        file = self.file
        for level in range(self.tree_level + 1):
            file = file.parent
        if not file.is_dir():
            raise NotADirectoryError
        return file

    def is_debug(self):
        return self.get_directory().name != 'site-packages'

    def chdir(self):
        os.chdir(self.get_directory())
