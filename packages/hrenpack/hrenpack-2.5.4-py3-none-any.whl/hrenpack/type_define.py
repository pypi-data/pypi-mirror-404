from typing import Optional


def is_int(data) -> bool:
    try:
        int(data)
    except ValueError:
        return False
    else:
        return True


def is_float(data) -> bool:
    try:
        float(data)
    except ValueError:
        return False
    else:
        return True


def is_bool(data) -> bool:
    try:
        bool(data)
    except ValueError:
        return False
    else:
        return True


class TypeEdit:
    @staticmethod
    def string(input) -> str:
        return str(input)

    @staticmethod
    def integer(input) -> int:
        return int(input)

    @staticmethod
    def float(input) -> float:
        return float(input)

    @staticmethod
    def boolean(input):
        if input is True or input.lower() == 'true':
            return True
        elif input is False or input.lower() == 'False':
            return False
        else:
            raise ValueError

    def isString(self, input, isString):
        return self.string(input) if isString else input

    def isInt(self, input, isInt):
        return self.integer(input) if isInt else input

    def isFloat(self, input, isFloat):
        return self.float(input) if isFloat else input

    def isBool(self, input, isBool):
        return self.boolean(input) if isBool else input


def isinstance_multi(obj, *types) -> bool:
    return isinstance(obj, types)


def issubclass_multi(obj, *classes) -> bool:
    return issubclass(obj, classes)


def is_object(arg, return_none: bool = True) -> Optional[bool]:
    if isinstance(arg, type):
        return False
    elif isinstance(arg, object):
        return True
    else:
        if return_none:
            return None
        else:
            return True
