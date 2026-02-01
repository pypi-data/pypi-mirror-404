class SlotsReadMixin:
    def __getitem__(self, item):
        if item in self.__slots__:
            return getattr(self, item)
        raise KeyError(item)


class SlotsMixin(SlotsReadMixin):
    def __setitem__(self, key, value):
        setattr(self, key, value)


class LogMixin:
    def log(self, *values, sep: str = ' ', end: str = '\n', file=None, flush: bool = False):
        if self.log_mode:
            print(*values, sep=sep, end=end, file=file, flush=flush)


class LogPlusMixin(LogMixin):
    log: bool = False
