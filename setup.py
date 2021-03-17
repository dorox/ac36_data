from distutils.core import setup
import os

data = []
for path, subdirs, files in os.walk("ac36data/"):
    for name in files:
        i = os.path.join(path, name)
        data.append(os.path.relpath(i, "ac36data"))

setup(
    name="ac36data",
    version="0.3.21",
    packages=["ac36data"],
    package_data={"ac36data": data},
)
