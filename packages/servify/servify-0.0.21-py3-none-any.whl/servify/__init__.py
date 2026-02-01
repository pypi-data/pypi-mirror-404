from .commons import servify_read

_reader: servify_read | None = None


def read_data(path: str, formato: str, **kwargs):
    global _reader
    if _reader is None:
        _reader = servify_read()

    return _reader.read_data(path, formato, **kwargs)


__all__ = ["read_data", "servify_read"]
