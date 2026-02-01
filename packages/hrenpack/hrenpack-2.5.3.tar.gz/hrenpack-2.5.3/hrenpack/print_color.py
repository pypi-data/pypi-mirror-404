from hrenpack.classes import DataClass


class ColorsANSI(DataClass):
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    RESET = '\033[0m'
    DICT = {
        'black': BLACK, 'red': RED, 'green': GREEN, 'yellow': YELLOW, 'blue': BLUE,
        'magenta': MAGENTA, 'cyan': CYAN, 'white': WHITE, 'reset': RESET,
        "черный": BLACK, "красный": RED, "зеленый": GREEN, "желтый": YELLOW, "синий": BLUE,
        "пурпурный": MAGENTA, "бирюзовый": CYAN, "белый": WHITE, "сброс": RESET
    }


def print_color(*values, color: str, separator: str = ' ', end: str = '\n', file=None) -> None:
    text = separator.join(values)
    text = ColorsANSI.DICT[color] + text + '\033[0m'
    print(text, end=end, file=file)


def print_error(*values, separator: str = ' ', end: str = '\n', file=None) -> None:
    print_color(*values, color='red', separator=separator, end=end, file=file)


def print_success(*values, separator: str = ' ', end: str = '\n', file=None) -> None:
    print_color(*values, color='green', separator=separator, end=end, file=file)


def print_warning(*values, separator: str = ' ', end: str = '\n', file=None) -> None:
    print_color(*values, color='yellow', separator=separator, end=end, file=file)


def print_info(*values, separator: str = ' ', end: str = '\n', file=None) -> None:
    print_color(*values, color='blue', separator=separator, end=end, file=file)


def color_format(*values, color: str, separator: str = ' ', end: str = '') -> str:
    text = separator.join(values)
    text = ColorsANSI.DICT[color] + text + '\033[0m'
    text += end
    return text


def error_format(*values, separator: str = ' ', end: str = '') -> str:
    return color_format(*values, color='red', separator=separator, end=end)


def success_format(*values, separator: str = ' ', end: str = '') -> str:
    return color_format(*values, color='green', separator=separator, end=end)


def warning_format(*values, separator: str = ' ', end: str = '') -> str:
    return color_format(*values, color='yellow', separator=separator, end=end)


def info_format(*values, separator: str = ' ', end: str = '') -> str:
    return color_format(*values, color='blue', separator=separator, end=end)
