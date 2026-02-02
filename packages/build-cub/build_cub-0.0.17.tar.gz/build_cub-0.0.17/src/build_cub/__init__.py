"""Build Cub package.

A dynamic versioning, Cython, PyBind11, and Raw C API building. Experimental.
"""

from build_cub._internal.cli import main
from build_cub._internal.info import METADATA

__version__: str = METADATA.version

__all__: list[str] = ["METADATA", "__version__", "main"]
