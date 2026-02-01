
# Explicitly re-export public API and internal helper
from .newwave import open, Error, Wave_read, Wave_write, _byteswap

__all__ = ["open", "Error", "Wave_read", "Wave_write"]

