from distutils.core import setup

setup(
    name="ac36data",
    version="0.1",
    packages=["ac36data"],
    package_dir={"ac36data": "ac36data"},
    package_data={"": ["./ac36data/*"]},
)
