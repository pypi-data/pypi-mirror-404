import time, datetime
from datetime import datetime as dt, date as date_object
from dataclasses import dataclass
from typing import Union, Optional, Literal
from hrenpack.listwork import intlist, strlist


# class DateTime:
#     @dataclass
#     class Data:
#         year: int
#         month: int
#         month_eng: str
#         month_rus: str
#         day: int
#         hour: int
#         minute: int
#         second: int
#         tick: int
#
#     @dataclass
#     class Calendar:
#         calendar: tuple
#         winter: tuple
#         spring: tuple
#         summer: tuple
#         autumn: tuple
#         winter_time: tuple
#         summer_time: tuple
#
#     @property
#     def calendar(self):
#         return (
#             '01.01', '02.01', '03.01', '04.01', '05.01', '06.01', '07.01', '08.01', '09.01', '10.01', '11.01', '12.01',
#             '13.01', '14.01', '15.01', '16.01', '17.01', '18.01', '19.01', '20.01', '21.01', '22.01', '23.01', '24.01',
#             '25.01', '26.01', '27.01', '28.01', '29.01', '30.01', '31.01', '01.02', '02.02', '03.02', '04.02', '05.02',
#             '06.02', '07.02', '08.02', '09.02', '10.02', '11.02', '12.02', '13.02', '14.02', '15.02', '16.02', '17.02',
#             '18.02', '19.02', '20.02', '21.02', '22.02', '23.02', '24.02', '25.02', '26.02', '27.02', '28.02', '29.02',
#             '01.03', '02.03', '03.03', '04.03', '05.03', '06.03', '07.03', '08.03', '09.03', '10.03', '11.03', '12.03',
#             '13.03', '14.03', '15.03', '16.03', '17.03', '18.03', '19.03', '20.03', '21.03', '22.03', '23.03', '24.03',
#             '25.03', '26.03', '27.03', '28.03', '29.03', '30.03', '31.03', '01.04', '02.04', '03.04', '04.04', '05.04',
#             '06.04', '07.04', '08.04', '09.04', '10.04', '11.04', '12.04', '13.04', '14.04', '15.04', '16.04', '17.04',
#             '18.04', '19.04', '20.04', '21.04', '22.04', '23.04', '24.04', '25.04', '26.04', '27.04', '28.04', '29.04',
#             '30.04', '01.05', '02.05', '03.05', '04.05', '05.05', '06.05', '07.05', '08.05', '09.05', '10.05', '11.05',
#             '12.05', '13.05', '14.05', '15.05', '16.05', '17.05', '18.05', '19.05', '20.05', '21.05', '22.05', '23.05',
#             '24.05', '25.05', '26.05', '27.05', '28.05', '29.05', '30.05', '31.05', '01.06', '02.06', '03.06', '04.06',
#             '05.06', '06.06', '07.06', '08.06', '09.06', '10.06', '11.06', '12.06', '13.06', '14.06', '15.06', '16.06',
#             '17.06', '18.06', '19.06', '20.06', '21.06', '22.06', '23.06', '24.06', '25.06', '26.06', '27.06', '28.06',
#             '29.06', '30.06', '01.07', '02.07', '03.07', '04.07', '05.07', '06.07', '07.07', '08.07', '09.07', '10.07',
#             '11.07', '12.07', '13.07', '14.07', '15.07', '16.07', '17.07', '18.07', '19.07', '20.07', '21.07', '22.07',
#             '23.07', '24.07', '25.07', '26.07', '27.07', '28.07', '29.07', '30.07', '31.07', '01.08', '02.08', '03.08',
#             '04.08', '05.08', '06.08', '07.08', '08.08', '09.08', '10.08', '11.08', '12.08', '13.08', '14.08', '15.08',
#             '16.08', '17.08', '18.08', '19.08', '20.08', '21.08', '22.08', '23.08', '24.08', '25.08', '26.08', '27.08',
#             '28.08', '29.08', '30.08', '31.08', '01.09', '02.09', '03.09', '04.09', '05.09', '06.09', '07.09', '08.09',
#             '09.09', '10.09', '11.09', '12.09', '13.09', '14.09', '15.09', '16.09', '17.09', '18.09', '19.09', '20.09',
#             '21.09', '22.09', '23.09', '24.09', '25.09', '26.09', '27.09', '28.09', '29.09', '30.09', '01.10', '02.10',
#             '03.10', '04.10', '05.10', '06.10', '07.10', '08.10', '09.10', '10.10', '11.10', '12.10', '13.10', '14.10',
#             '15.10', '16.10', '17.10', '18.10', '19.10', '20.10', '21.10', '22.10', '23.10', '24.10', '25.10', '26.10',
#             '27.10', '28.10', '29.10', '30.10', '31.10', '01.11', '02.11', '03.11', '04.11', '05.11', '06.11', '07.11',
#             '08.11', '09.11', '10.11', '11.11', '12.11', '13.11', '14.11', '15.11', '16.11', '17.11', '18.11', '19.11',
#             '20.11', '21.11', '22.11', '23.11', '24.11', '25.11', '26.11', '27.11', '28.11', '29.11', '30.11', '01.12',
#             '02.12', '03.12', '04.12', '05.12', '06.12', '07.12', '08.12', '09.12', '10.12', '11.12', '12.12', '13.12',
#             '14.12', '15.12', '16.12', '17.12', '18.12', '19.12', '20.12', '21.12', '22.12', '23.12', '24.12', '25.12',
#             '26.12', '27.12', '28.12', '29.12', '30.12', '31.12'
#         )
#
#     @property
#     def winter(self):
#         return (
#             '01.12', '02.12', '03.12', '04.12', '05.12', '06.12', '07.12', '08.12', '09.12', '10.12', '11.12', '12.12',
#             '13.12', '14.12', '15.12', '16.12', '17.12', '18.12', '19.12', '20.12', '21.12', '22.12', '23.12', '24.12',
#             '25.12', '26.12', '27.12', '28.12', '29.12', '30.12', '31.12', '01.01', '02.01', '03.01', '04.01', '05.01',
#             '06.01', '07.01', '08.01', '09.01', '10.01', '11.01', '12.01', '13.01', '14.01', '15.01', '16.01', '17.01',
#             '18.01', '19.01', '20.01', '21.01', '22.01', '23.01', '24.01', '25.01', '26.01', '27.01', '28.01', '29.01',
#             '30.01', '31.01', '01.02', '02.02', '03.02', '04.02', '05.02', '06.02', '07.02', '08.02', '09.02', '10.02',
#             '11.02', '12.02', '13.02', '14.02', '15.02', '16.02', '17.02', '18.02', '19.02', '20.02', '21.02', '22.02',
#             '23.02', '24.02', '25.02', '26.02', '27.02', '28.02', '29.02'
#         )
#
#     @property
#     def spring(self):
#          return (
#             '01.03', '02.03', '03.03', '04.03', '05.03', '06.03', '07.03', '08.03', '09.03', '10.03', '11.03', '12.03',
#             '13.03', '14.03', '15.03', '16.03', '17.03', '18.03', '19.03', '20.03', '21.03', '22.03', '23.03', '24.03',
#             '25.03', '26.03', '27.03', '28.03', '29.03', '30.03', '31.03', '01.04', '02.04', '03.04', '04.04', '05.04',
#             '06.04', '07.04', '08.04', '09.04', '10.04', '11.04', '12.04', '13.04', '14.04', '15.04', '16.04', '17.04',
#             '18.04', '19.04', '20.04', '21.04', '22.04', '23.04', '24.04', '25.04', '26.04', '27.04', '28.04', '29.04',
#             '30.04', '01.05', '02.05', '03.05', '04.05', '05.05', '06.05', '07.05', '08.05', '09.05', '10.05', '11.05',
#             '12.05', '13.05', '14.05', '15.05', '16.05', '17.05', '18.05', '19.05', '20.05', '21.05', '22.05', '23.05',
#             '24.05', '25.05', '26.05', '27.05', '28.05', '29.05', '30.05', '31.05'
#         )
#
#     @property
#     def summer(self):
#         return (
#             '01.06', '02.06', '03.06', '04.06', '05.06', '06.06', '07.06', '08.06', '09.06', '10.06', '11.06', '12.06',
#             '13.06', '14.06', '15.06', '16.06', '17.06', '18.06', '19.06', '20.06', '21.06', '22.06', '23.06', '24.06',
#             '25.06', '26.06', '27.06', '28.06', '29.06', '30.06', '01.07', '02.07', '03.07', '04.07', '05.07', '06.07',
#             '07.07', '08.07', '09.07', '10.07', '11.07', '12.07', '13.07', '14.07', '15.07', '16.07', '17.07', '18.07',
#             '19.07', '20.07', '21.07', '22.07', '23.07', '24.07', '25.07', '26.07', '27.07', '28.07', '29.07', '30.07',
#             '31.07', '01.08', '02.08', '03.08', '04.08', '05.08', '06.08', '07.08', '08.08', '09.08', '10.08', '11.08',
#             '12.08', '13.08', '14.08', '15.08', '16.08', '17.08', '18.08', '19.08', '20.08', '21.08', '22.08', '23.08',
#             '24.08', '25.08', '26.08', '27.08', '28.08', '29.08', '30.08', '31.08'
#         )
#
#     @property
#     def autumn(self):
#         return (
#             '01.09', '02.09', '03.09', '04.09', '05.09', '06.09', '07.09', '08.09', '09.09', '10.09', '11.09', '12.09',
#             '13.09', '14.09', '15.09', '16.09', '17.09', '18.09', '19.09', '20.09', '21.09', '22.09', '23.09', '24.09',
#             '25.09', '26.09', '27.09', '28.09', '29.09', '30.09', '01.10', '02.10', '03.10', '04.10', '05.10', '06.10',
#             '07.10', '08.10', '09.10', '10.10', '11.10', '12.10', '13.10', '14.10', '15.10', '16.10', '17.10', '18.10',
#             '19.10', '20.10', '21.10', '22.10', '23.10', '24.10', '25.10', '26.10', '27.10', '28.10', '29.10', '30.10',
#             '31.10', '01.11', '02.11', '03.11', '04.11', '05.11', '06.11', '07.11', '08.11', '09.11', '10.11', '11.11',
#             '12.11', '13.11', '14.11', '15.11', '16.11', '17.11', '18.11', '19.11', '20.11', '21.11', '22.11', '23.11',
#             '24.11', '25.11', '26.11', '27.11', '28.11', '29.11', '30.11'
#         )
#
#     winter_time = (
#         '31.10', '01.11', '02.11', '03.11', '04.11', '05.11', '06.11', '07.11', '08.11', '09.11', '10.11', '11.11',
#         '12.11', '13.11', '14.11', '15.11', '16.11', '17.11', '18.11', '19.11', '20.11', '21.11', '22.11', '23.11',
#         '24.11', '25.11', '26.11', '27.11', '28.11', '29.11', '30.11', '01.12', '02.12', '03.12', '04.12', '05.12',
#         '06.12', '07.12', '08.12', '09.12', '10.12', '11.12', '12.12', '13.12', '14.12', '15.12', '16.12', '17.12',
#         '18.12', '19.12', '20.12', '21.12', '22.12', '23.12', '24.12', '25.12', '26.12', '27.12', '28.12', '29.12',
#         '30.12', '31.12', '01.01', '02.01', '03.01', '04.01', '05.01', '06.01', '07.01', '08.01', '09.01', '10.01',
#         '11.01', '12.01', '13.01', '14.01', '15.01', '16.01', '17.01', '18.01', '19.01', '20.01', '21.01', '22.01',
#         '23.01', '24.01', '25.01', '26.01', '27.01', '28.01', '29.01', '30.01', '31.01', '01.02', '02.02', '03.02',
#         '04.02', '05.02', '06.02', '07.02', '08.02', '09.02', '10.02', '11.02', '12.02', '13.02', '14.02', '15.02',
#         '16.02', '17.02', '18.02', '19.02', '20.02', '21.02', '22.02', '23.02', '24.02', '25.02', '26.02', '27.02',
#         '28.02', '29.02', '01.03', '02.03', '03.03', '04.03', '05.03', '06.03', '07.03', '08.03', '09.03', '10.03',
#         '11.03', '12.03', '13.03', '14.03', '15.03', '16.03', '17.03', '18.03', '19.03', '20.03', '21.03', '22.03',
#         '23.03', '24.03', '25.03', '26.03', '27.03', '28.03', '29.03', '30.03'
#     )
#     summer_time = (
#         '31.03', '01.04', '02.04', '03.04', '04.04', '05.04', '06.04', '07.04', '08.04', '09.04', '10.04', '11.04',
#         '12.04', '13.04', '14.04', '15.04', '16.04', '17.04', '18.04', '19.04', '20.04', '21.04', '22.04', '23.04',
#         '24.04', '25.04', '26.04', '27.04', '28.04', '29.04', '30.04', '01.05', '02.05', '03.05', '04.05', '05.05',
#         '06.05', '07.05', '08.05', '09.05', '10.05', '11.05', '12.05', '13.05', '14.05', '15.05', '16.05', '17.05',
#         '18.05', '19.05', '20.05', '21.05', '22.05', '23.05', '24.05', '25.05', '26.05', '27.05', '28.05', '29.05',
#         '30.05', '31.05', '01.06', '02.06', '03.06', '04.06', '05.06', '06.06', '07.06', '08.06', '09.06', '10.06',
#         '11.06', '12.06', '13.06', '14.06', '15.06', '16.06', '17.06', '18.06', '19.06', '20.06', '21.06', '22.06',
#         '23.06', '24.06', '25.06', '26.06', '27.06', '28.06', '29.06', '30.06', '01.07', '02.07', '03.07', '04.07',
#         '05.07', '06.07', '07.07', '08.07', '09.07', '10.07', '11.07', '12.07', '13.07', '14.07', '15.07', '16.07',
#         '17.07', '18.07', '19.07', '20.07', '21.07', '22.07', '23.07', '24.07', '25.07', '26.07', '27.07', '28.07',
#         '29.07', '30.07', '31.07', '01.08', '02.08', '03.08', '04.08', '05.08', '06.08', '07.08', '08.08', '09.08',
#         '10.08', '11.08', '12.08', '13.08', '14.08', '15.08', '16.08', '17.08', '18.08', '19.08', '20.08', '21.08',
#         '22.08', '23.08', '24.08', '25.08', '26.08', '27.08', '28.08', '29.08', '30.08', '31.08', '01.09', '02.09',
#         '03.09', '04.09', '05.09', '06.09', '07.09', '08.09', '09.09', '10.09', '11.09', '12.09', '13.09', '14.09',
#         '15.09', '16.09', '17.09', '18.09', '19.09', '20.09', '21.09', '22.09', '23.09', '24.09', '25.09', '26.09',
#         '27.09', '28.09', '29.09', '30.09', '01.10', '02.10', '03.10', '04.10', '05.10', '06.10', '07.10', '08.10',
#         '09.10', '10.10', '11.10', '12.10', '13.10', '14.10', '15.10', '16.10', '17.10', '18.10', '19.10', '20.10',
#         '21.10', '22.10', '23.10', '24.10', '25.10', '26.10', '27.10', '28.10', '29.10', '30.10'
#     )
#     __calendar__ = Calendar(calendar, winter, spring, summer,
#                             autumn, winter_time, summer_time)
#
#     def now(self) -> Data:
#         def lmonth(month: int, translate: bool = False):
#             russian = ("Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август",
#                        "Сентябрь", "Октябрь", "Ноябрь", "Декабрь")
#             english = ('January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
#                        'September', 'October', 'November', 'December')
#             i = month - 1
#             r, e = russian[i], english[i]
#             return r if translate else e
#
#         now = dt.now()
#         m = now.month
#         return self.Data(now.year, m, lmonth(m, False), lmonth(m, True),
#                          now.day, now.hour, now.minute, now.second, now.microsecond)


class HoursMinutesAndSeconds:
    def __init__(self, hours: int = 0, minutes: int = 0, seconds: int = 0):
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds
        self.__time_format()

    def __str__(self):
        h, m, s = self.hours, self.minutes, self.seconds
        h = str(h).zfill(2)
        m = str(m).zfill(2)
        s = str(s).zfill(2)
        return '{}:{}:{}'.format(h, m, s)

    def __int__(self):
        return self.to_seconds()

    def __bool__(self):
        return self.to_seconds() != 0

    def __add__(self, other):
        if type(other) is HoursMinutesAndSeconds:
            h = self.hours + other.hours
            m = self.minutes + other.minutes
            s = self.seconds + other.seconds
        elif type(other) is str:
            h, m, s = other.split(':')
            h = int(h) + self.hours
            m = int(m) + self.minutes
            s = int(s) + self.seconds
        elif type(other) is int:
            h, m, s = self.hours, self.minutes, self.seconds
            s += other
            h, m, s = time_format(h, m, s)
        else:
            raise ValueError('HoursMinutesAndSeconds can add with int, str or HoursMinutesAndSeconds')
        return HoursMinutesAndSeconds(h, m, s)

    def __sub__(self, other):
        if type(other) is HoursMinutesAndSeconds:
            h = self.hours - other.hours
            m = self.minutes - other.minutes
            s = self.seconds - other.seconds
        elif type(other) is str:
            h, m, s = other.split(':')
            h = int(h) - self.hours
            m = int(m) - self.minutes
            s = int(s) - self.seconds
        elif type(other) is int:
            h, m, s = self.hours, self.minutes, self.seconds
            s -= other
            # h, m, s = time_format(h, m, s)
        else:
            raise ValueError('From HoursMinutesAndSeconds can subtract int, str or HoursMinutesAndSeconds')
        return HoursMinutesAndSeconds(h, m, s)

    def __mul__(self, other: int):
        h = self.hours * other
        m = self.minutes * other
        s = self.seconds * other
        return HoursMinutesAndSeconds(h, m, s)

    def __time_format(self):
        while self.seconds >= 60:
            self.seconds -= 60
            self.minutes += 1
        while self.minutes >= 60:
            self.minutes -= 60
            self.hours += 1

    @classmethod
    def from_seconds(cls, seconds: int):
        return cls(*time_format(0, 0, seconds))

    @classmethod
    def from_string(cls, string: str, separator: str = ':', ms: Optional[bool] = None):
        slist = string.split(separator)
        if slist.__len__() == 3:
            h, m, s = string.split(separator)
        elif slist.__len__() == 2:
            if ms is None:
                raise ValueError('Если используются только 2 аргумента, то параметр ms должен быть булевым значением')
            elif ms:
                h = 0
                m, s = slist
            else:
                h, m = slist
                s = 0
        else:
            raise ValueError("Аргументов должно быть либо 2, либо 3")
        return cls(int(h), int(m), int(s))

    def to_seconds(self) -> int:
        return self.hours * 3600 + self.minutes * 60 + self.seconds


def time_format(hours: int, minutes: int, seconds: int, return_mode: Literal['string', 'tuple', 'class'] = 'tuple'):
    while seconds >= 60:
        seconds -= 60
        minutes += 1
    while minutes >= 60:
        minutes -= 60
        hours += 1
    output = {
        'string': '{}:{}:{}'.format(hours, minutes, seconds),
        'tuple': (hours, minutes, seconds),
        'class': HoursMinutesAndSeconds(hours, minutes, seconds)
    }
    return output[return_mode]


def datetime_format(input: int):
    return '0' + str(input) if input < 10 else str(input)


def date_and_time_data():
    @dataclass
    class Data:
        date: str
        time: str

    now = dt.now()
    date = f'{datetime_format(now.day)}.{datetime_format(now.month)}.{now.year}'
    time = f'{datetime_format(now.hour)}:{datetime_format(now.minute)}:{datetime_format(now.second)}'
    return Data(date, time)


def date(year: bool) -> str:
    now = dt.now()
    data = f'{now.day}.{now.month}'
    return data + f'.{now.year}' if year else data


def time_summ(*args: Union[str, HoursMinutesAndSeconds], return_hms: bool = False):
    args = list(args)
    first = args[0]
    output = HoursMinutesAndSeconds.from_string(first) if type(first) is str else first
    args.pop(0)
    for arg in args:
        output += arg
    return output if return_hms else str(output)


def perf_counter(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        func(*args, **kwargs)
        end = time.perf_counter()
        print(end - start)

    return wrapper


def unix_to_datetime(unix_timestamp: int) -> dt:
    return dt.fromtimestamp(unix_timestamp)


def datetime_to_time(input: dt) -> datetime.time:
    return datetime.time(input.hour, input.minute, input.second)


def string_to_datetime(input: str, dt_separator: str = ' ', date_separator: str = '.', time_separator: str = ':',
                       date_reverse: bool = False) -> dt:
    date, time = input.split(dt_separator)
    date = intlist(date.split(date_separator))
    time = intlist(time.split(time_separator))
    if date_reverse:
        date = list(reversed(date))
    return dt(*date, *time)


def string_to_date(input: str, date_separator: str = '.', date_reverse: bool = False) -> dt:
    return string_to_datetime(input + ' 00:00:00', date_separator=date_separator, date_reverse=date_reverse)


def zero_form(input: Union[str, int]):
    if isinstance(input, str):
        input = int(input)
    return str(input) if input > 9 else '0' + str(input)


def zero_str(input: Union[str, dt]):
    if isinstance(input, str):
        output = input.split(':')
        if len(output) == 2:
            h, m = output
            return ':'.join([zero_form(h), zero_form(m)])
        elif len(output) == 3:
            h, m, s = output
            return ':'.join([zero_form(h), zero_form(m), zero_form(s)])
        else:
            raise ValueError
    else:
        h, m, s = input.hour, input.minute, input.second
        return ':'.join([zero_form(h), zero_form(m), zero_form(s)])


def datetime_to_str(input: dt, mode: Literal['date', 'time', 'datetime'] = 'datetime',
                    date_separator: str = '.', time_separator: str = ':', without_seconds: bool = False,
                    date_order: Literal['dmy', 'dym', 'mdy', 'myd', 'ydm', 'ymd'] = 'dmy') -> str:
    match date_order:
        case 'dmy':
            dym_tup = [input.day, input.month, input.year]
        case 'dym':
            dym_tup = [input.day, input.year, input.month]
        case 'mdy':
            dym_tup = [input.month, input.day, input.year]
        case 'myd':
            dym_tup = [input.month, input.year, input.day]
        case 'ydm':
            dym_tup = [input.year, input.day, input.month]
        case 'ymd':
            dym_tup = [input.year, input.month, input.day]
        case _:
            raise ValueError

    for i in range(3):
        if dym_tup[i] < 10:
            dym_tup[i] = '0' + str(dym_tup[i])

    date = date_separator.join(strlist(dym_tup))
    time = time_separator.join(
        strlist((input.hour, input.minute) if without_seconds else (input.hour, input.minute, input.second))
    )

    match mode:
        case 'date':
            return date
        case 'time':
            return time
        case 'datetime':
            return f'{date} {time}'
        case _:
            raise ValueError


def now_to_str(mode: Literal['date', 'time', 'datetime'] = 'datetime',
               date_separator: str = '.', time_separator: str = ':', without_seconds: bool = False,
               date_order: Literal['dmy', 'dym', 'mdy', 'myd', 'ydm', 'ymd'] = 'dmy'):
    return datetime_to_str(dt.now(), mode, date_separator, time_separator, without_seconds, date_order)


def datetime_to_date_object(input: dt) -> date_object:
    return date_object(day=input.day, month=input.month, year=input.year)
