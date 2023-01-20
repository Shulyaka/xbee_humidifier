"""Install bundle."""

import machine
import uos

bundle_list = [
    "lib/core.mpy",
    "lib/tosr0x.mpy",
    "lib/mainloop.mpy",
    "lib/tosr.mpy",
    "lib/xbeepin.mpy",
    "lib/humidifier.mpy",
    "commands.mpy",
    "dutycycle.mpy",
    "config.mpy",
    "main.py",
]

if "bundle.py" in uos.listdir("/flash"):
    # First stage: compile files
    uos.chdir("/flash/lib")
    for file in uos.listdir():
        if file[-3:] == ".py":
            uos.compile(file)
            uos.remove(file)
    uos.chdir("/flash")
    for file in uos.listdir():
        if file[-3:] == ".py":
            uos.compile(file)
            if file != "bundle.py":
                uos.remove(file)
    uos.remove("bundle.py")
    uos.sync()

    # Second stage: bundle
    uos.bundle(*bundle_list)  # This will trigger soft reset!

elif "bundle.mpy" in uos.listdir("/flash"):
    # Third stage: delete bundled files
    uos.chdir("/flash")
    for file in bundle_list:
        uos.remove(file)
    uos.remove("bundle.mpy")
    uos.sync()
    machine.soft_reset()
