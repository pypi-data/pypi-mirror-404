import sys
from importlib.metadata import version as _get_version

__version__ = _get_version("pathbridge")

version = f"{__version__}, Python {sys.version}"
