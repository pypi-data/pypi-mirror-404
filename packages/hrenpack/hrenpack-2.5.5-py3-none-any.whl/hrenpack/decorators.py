import os, sys, logging, warnings
from typing import Optional, LiteralString
from contextlib import redirect_stdout, nullcontext
from functools import wraps
from hrenpack.listwork import key_in_dict


if sys.version_info >= (3, 13):
    from warnings import deprecated
else:
    class deprecated:
        warnings.warn('Use warnings.deprecated or DeprecatedWarning instead', DeprecationWarning, stacklevel=2)

        def __init__(self, message: LiteralString, /, *,
                     category: type[Warning] = DeprecationWarning,
                     stacklevel: int = 1):
            self.message = message
            self.category = category
            self.stacklevel = stacklevel

        def _decorate_function(self, func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                warnings.warn(self.message, self.category, self.stacklevel)
                return func(*args, **kwargs)

            wrapper.__deprecated__ = True
            return wrapper

        def _decorate_class(self, cls: type):
            init = cls.__init__

            @wraps(init)
            def new_init(self, *args, **kwargs):
                warnings.warn(self.message, self.category, self.stacklevel)
                return init(self, *args, **kwargs)

            cls.__init__ = new_init
            cls.__deprecated__ = True
            cls.__deprecated_message__ = self.message
            return cls

        def __call__(self, decorated):
            if sys.version_info >= (3, 13):
                return warnings.deprecated(self.message, category=self.category, stacklevel=self.stacklevel)(decorated)
            elif isinstance(decorated, type):
                return self._decorate_class(decorated)
            else:
                return self._decorate_function(decorated)


def confirm(inp_text: str = "Вы уверены, что хотите выполнить эту программу?"):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = input(inp_text + "\nВведите y, д или 1, если да, или n, н или 0, если нет\n")
            while True:
                if result in ('y', 'Y', "д", "Д", "1"):
                    return func(*args, **kwargs)
                elif result in ('n', 'N', "н", "Н", "0"):
                    break
                else:
                    result = input(inp_text + "\nВведите y, д или 1, если да, или n, н или 0, если нет\n")

        return wrapper
    return decorator


def non_print(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with redirect_stdout(nullcontext()):
            return func(*args, **kwargs)
    return wrapper


def args_kwargs(**kwargs):
    args_name = kwargs.get('args_name', 'args')
    kwargs_name = kwargs.get('kwargs_name', 'kwargs')
    copy_args = kwargs.get('copy_args', True)
    copy_kwargs = kwargs.get('copy_kwargs', True)
    del_kwargs = kwargs.get('del_kwargs', True)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **key_args):
            if key_in_dict(key_args, args_name) and copy_args:
                args = [*args, *key_args[args_name]]
                if del_kwargs:
                    del key_args[args_name]
            if key_in_dict(key_args, kwargs_name) and copy_kwargs:
                key_args = {**key_args, **key_args[kwargs_name]}
                if del_kwargs:
                    del key_args[kwargs_name]
            return func(*args, **key_args)
        return wrapper
    return decorator


def debug_logging(start_message: str = '', end_message: str = ''):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if start_message:
                logging.debug(start_message)
            output = func(*args, **kwargs)
            if end_message:
                logging.debug(end_message)
            return output
        return wrapper
    return decorator


def method(func):
    return func


def multi_decorator(*decorators):
    """Декораторы применяются слева направо"""
    def decorator(func):
        for dec in decorators:
            func = dec(func)
        return func
    return decorator
