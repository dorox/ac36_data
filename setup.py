from distutils.core import setup

setup(
    name="ac36data",
    version="0.1",
    py_modules=["data"],
    package_data={"": ["*/stats.bin", "*/boats.bin"]},
)
