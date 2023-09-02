"""Launch setup or start the program."""

try:
    import bundle  # noqa: F401
except ImportError:
    pass

from __init__ import main_loop

main_loop.run()

import logging  # noqa: E402

logging.getLogger(__name__).error("Main loop exited")
