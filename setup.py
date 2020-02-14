from setuptools import setup, find_packages
from pathlib import Path

with Path('README.md').open() as readme:
    readme = readme.read()

version = 0.2

setup(
    name='pysexpr',
    version=version if isinstance(version, str) else str(version),
    keywords="",
    description="",
    long_description=readme,
    long_description_content_type="text/markdown",
    license='mit',
    python_requires='>=3.6.0',
    url='https://github.com/thautawarm/PySExpr',
    author='thautawarm',
    author_email='twshere@outlook.com',
    packages=find_packages(),
    entry_points={"console_scripts": []},
    install_requires=['attrs>=19.3.0', 'bytecode>=0.10.0'],
    platforms="any",
    classifiers=[
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    zip_safe=False,
)
