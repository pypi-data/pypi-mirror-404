import argparse, sys, functools
from argparse import Namespace
from hrenpack.functionwork import empty_function
from hrenpack.iterwork import multi_in


def naih(method):
    @functools.wraps(method)
    def wrapper(self, args=None, namespace=None):
        if self._no_args_is_help:
            self.no_args_is_help()
        return getattr(super(type(self), self), method.__name__, empty_function)(args, namespace)
    return wrapper


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, **kwargs):
        self._no_args_is_help = kwargs.pop('no_args_is_help', False)
        self._version = kwargs.pop('version', None)
        self._add_quiet = kwargs.pop('add_quiet', False)
        super().__init__(**kwargs)
        if self._version is not None:
            self.add_argument('--version', '-v', action='version', version=self._version)
        if self._add_quiet:
            self.add_argument('--quiet', '-q', action='store_true')

    def no_args_is_help(self):
        if len(sys.argv) <= 1:
            self.print_help()
            sys.exit(0)

    @naih
    def parse_args(self, args = None, namespace = None) -> Namespace: pass

    @naih
    def parse_known_args(self, args = None, namespace = None) -> tuple[Namespace, list[str]]: pass

    @naih
    def parse_intermixed_args(self, args = None, namespace = None) -> Namespace: pass

    @naih
    def parse_known_intermixed_args(self, args = None, namespace = None) -> tuple[Namespace, list[str]]: pass

    @property
    def logging(self):
        return not multi_in(sys.argv, '--quiet', '-q')

    def log(self, *values, sep: str = ' ', end: str = '\n'):
        if self.logging:
            print(*values, sep=sep, end=end)
