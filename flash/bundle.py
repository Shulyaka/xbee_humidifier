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
    "tosr.mpy",
    "humidifier.mpy",
    "dutycycle.mpy",
    "config.mpy",
]

atcmd("AP", 0)

_all_compiled = True
for file in uos.listdir() + uos.listdir("lib"):
    if file[-3:] == ".py":
        _all_compiled = False
        break

# First stage: compile files
if not _all_compiled:
    opt_level(3)

    def compile_file(name):
        """Compile a single file."""
        try:
            uos.remove(name[:-3] + ".mpy")
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
            if filename[-3:] == ".py":
                compile_file(filename)
        uos.chdir(cwd)

    try:
        # First compile main.py and bundle.py
        if "main.py" in uos.listdir():
            compile_file("main.py")
        if "bundle.py" in uos.listdir():
            compile_file("bundle.py")
        compile_dir()
        compile_dir("lib")
    except MemoryError as e:
        print(type(e).__name__ + ": " + str(e))
    finally:
        uos.sync()
        machine.soft_reset()  # Retry or continue after reboot

# Second stage: bundle
uos.remove("bundle.mpy")
uos.sync()
collect()
uos.bundle(*_bundle_list)
