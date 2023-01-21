"""Launch setup or start the program."""

try:
    import bundle  # noqa: F401
except ImportError:
    pass

from __init__ import *  # noqa: F401, F403
