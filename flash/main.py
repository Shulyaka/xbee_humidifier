"""Launch setup or start the program."""

try:
    import bundle  # noqa: F401
except ImportError:
    pass

from __init__ import main_loop
from lib import logging

_LOGGER = logging.getLogger(__name__)

try:
    main_loop.run()
except Exception as e:
    _LOGGER.error("Mainloop exception: {}: {}".format(type(e).__name__, e))
else:
    _LOGGER.error("Mainloop exited")
