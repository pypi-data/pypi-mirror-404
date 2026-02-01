from setuptools import setup, find_packages

setup(
    name="dekoRL",
    version="1.0.0",
    author="MurilooPrDev",
    description="Deko: Rootless Container Engine & ISO Builder for Termux",
    packages=find_packages(),
    install_requires=["requests", "colorama"],
    entry_points={
        "console_scripts": [
            "deko=deko:main",
        ],
    },
    keywords=["deko", "termux", "container", "rootless", "iso", "linux"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
    ],
)
