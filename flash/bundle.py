"""Install bundle."""

from gc import collect

import machine
import uos
from micropython import opt_level
from xbee import atcmd

_bundle_list = [
    "lib/logging.mpy",
    "lib/core.mpy",
    "lib/mainloop.mpy",
    "lib/xbeepin.mpy",
    "tosr0x.mpy",
    "humidifier.mpy",
    "dutycycle.mpy",
    "commands.mpy",
]

atcmd("AP", 0)

# First stage: compile files
if any(file.endswith(".py") for file in uos.listdir() + uos.listdir("lib")):
    opt_level(3)

    def compile_file(name):
        """Compile a single file."""
        try:
            uos.remove(name.replace(".py", ".mpy"))
        except OSError:
            pass
        collect()
        uos.compile(name)
        uos.remove(name)

    def compile_dir(name="."):
        """Compile the files in directory (non-recursive)."""
        cwd = uos.getcwd()
        uos.chdir(name)
        for filename in uos.listdir():
            if filename.endswith(".py"):
                compile_file(filename)
        uos.chdir(cwd)

    try:
        # First compile main.py and bundle.py
        if "main.py" in uos.listdir():
            compile_file("main.py")
        if "bundle.py" in uos.listdir():
            compile_file("bundle.py")
            uos.bundle("bundle.mpy")
        compile_dir()
        compile_dir("lib")
    except MemoryError as e:
        print("{}: {}".format(type(e).__name__, e))
    finally:
        uos.sync()
        machine.soft_reset()  # Retry or continue after reboot

# Second stage: bundle
if "bundle" in uos.bundle():

    def _unbundle():
        uos.bundle(None)
        machine.soft_reset()

    _unbundle()
uos.remove("bundle.mpy")
uos.sync()
collect()
uos.bundle(*_bundle_list)
