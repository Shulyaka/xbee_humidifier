"""Install bundle."""

from gc import collect

import machine
import uos

bundle_list = [
    "lib/logging.mpy",
    "lib/core.mpy",
    "lib/tosr0x.mpy",
    "lib/mainloop.mpy",
    "lib/tosr.mpy",
    "lib/xbeepin.mpy",
    "lib/humidifier.mpy",
    "dutycycle.mpy",
    "__init__.mpy",
    "config.mpy",
]

all_compiled = True
for file in uos.listdir("/flash") + uos.listdir("/flash/lib"):
    if file[-3:] == ".py":
        all_compiled = False
        break

if not all_compiled:
    # First stage: compile files
    def compile_file(file):
        """Compile a single file."""
        try:
            uos.remove(file[:-3] + ".mpy")
        except OSError:
            pass
        collect()
        uos.compile(file)
        uos.remove(file)

    def compile_dir(name):
        """Compile the files in directory (non-recursive)."""
        uos.chdir(name)
        for file in uos.listdir():
            if file[-3:] == ".py":
                compile_file(file)

    try:
        # First compile main.py and bundle.py
        if "main.py" in uos.listdir("/flash"):
            compile_file("/flash/main.py")
        if "bundle.py" in uos.listdir("/flash"):
            compile_file("/flash/bundle.py")
        # First bundle bundle.mpy
        if "bundle.mpy" in uos.listdir("/flash") and "bundle" not in uos.bundle():
            uos.bundle("bundle.mpy")
        compile_dir("/flash/lib")
        compile_dir("/flash")
        uos.sync()
        print("Compiled successfully")
    except MemoryError as e:
        print(type(e).__name__ + ": " + str(e))
        uos.sync()
        machine.soft_reset()  # Retry after reboot

    # Second stage: bundle
    collect()
    uos.bundle(*bundle_list)  # This will trigger soft reset!

else:
    # Third stage: delete bundled files
    uos.chdir("/flash")
    if len(uos.bundle()) == 0:
        collect()
        uos.bundle(*bundle_list)  # Retry the bundle

    for file in uos.bundle():
        uos.remove(file + ".mpy")
    uos.remove("bundle.mpy")
    uos.sync()
    machine.soft_reset()
