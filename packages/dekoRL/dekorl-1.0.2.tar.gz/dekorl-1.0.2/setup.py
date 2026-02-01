from setuptools import setup, find_packages

setup(
    name="dekoRL",
    version="1.0.2",
    author="MurilooPrDev",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["colorama", "requests"],
    entry_points={
        "console_scripts": [
            "deko=deko_main:main",
        ],
    },
)
