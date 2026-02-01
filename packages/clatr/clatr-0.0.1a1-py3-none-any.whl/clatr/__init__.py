from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("clatr")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"