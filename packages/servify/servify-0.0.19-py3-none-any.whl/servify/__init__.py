from .commons import servify_read  # noqa: F401,F403

# Instância global automática
_reader = servify_read()

def read_data(path: str, formato: str, **kwargs):
    return _reader.helper_reading_data.read_data(path, formato, **kwargs)

__all__ = ["read_data", "servify_read"]