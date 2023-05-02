"""Setup module for xbee_humidifier."""

import pathlib

from setuptools import find_packages, setup

VERSION = "0.0.1"


def long_description():
    """Read README.md file."""
    f = (pathlib.Path(__file__).parent / "README.md").open()
    res = f.read()
    f.close()
    return res


setup(
    name="xbee_humidifier",
    version=VERSION,
    description="MicroPython firmware for a DIY humidifier",
    long_description=long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/Shulyaka/xbee_humidifier",
    author="Denis Shulyaka",
    author_email="ds_github@shulyaka.org.ru",
    license="GNU General Public License v3.0",
    keywords="xbee micropython humidifier",
    packages=find_packages(exclude=["tests"]),
    python_requires=">=3.7",
    tests_require=["pytest"],
)
