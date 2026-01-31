
from __future__ import annotations

from . import regorus as _native  # the compiled extension

# Re-export the API you want at top-level
Engine = _native.Engine

__all__ = ["Engine"]
