from builtins import __polyglot__

class PolyglotObject:
    def __new__(cls):
        Type = __polyglot__.require(cls.__typename__)
        return Type()