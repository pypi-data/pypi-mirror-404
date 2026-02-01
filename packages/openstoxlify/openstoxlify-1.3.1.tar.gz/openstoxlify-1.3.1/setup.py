from setuptools import setup, find_packages

setup(
    packages=find_packages(include=["openstoxlify", "openstoxlify.*"]),
    include_package_data=True,
)
