import platform, ctypes
from ctypes import wintypes
from typing import Union
from screeninfo import get_monitors


class ResolutionNotFoundError(Exception):
    pass


def get_monitor_info(monitor: int = 0):
    return get_monitors()[monitor]


def get_primary_monitor_info():
    for monitor in get_monitors():
        if monitor.is_primary:
            return monitor


def get_resolution(monitor: int = 0, letter: str = '') -> Union[tuple[int, int], str]:
    monitor_info = get_monitor_info(monitor)
    width, height = monitor_info.width, monitor_info.height
    return (width, height) if letter == '' else f'{width}{letter}{height}'


def resolution_function(**resolutions):
    """kwarg example: r1920x1080=func"""
    resolution = get_resolution(letter='x')
    rr = 'r' + resolution
    if rr in resolutions:
        resolutions[rr]()
    elif 'default' in resolutions:
        resolutions['default']()
    else:
        raise ResolutionNotFoundError('Вашего разрешения нет в списке')


def resolution_return(**resolutions):
    """kwarg example: r1920x1080=value"""
    resolution = get_resolution(letter='x')
    rr = 'r' + resolution
    if rr in resolutions:
        return resolutions[rr]
    elif 'default' in resolutions:
        return resolutions['default']
    else:
        raise ResolutionNotFoundError('Вашего разрешения нет в списке')


def get_refresh_rate():
    if platform.system() == 'Windows':
        import win32api
        import win32con
        return win32api.EnumDisplaySettings(None, win32con.ENUM_CURRENT_SETTINGS).DisplayFrequency
    else:
        raise OSError("Данная функция работает только на Windows")
