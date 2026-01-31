"""EmDash Core - FastAPI server for code intelligence."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("emdash-core")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"
