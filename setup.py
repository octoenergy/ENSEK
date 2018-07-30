#!/usr/bin/env python
# -*- coding: utf-8 -*
import io
import os

from setuptools import find_packages, setup

NAME = 'ENSEK'
DESCRIPTION = (
    'Python Client for the ENSEK API (http://www.ensek.co.uk/) '
)
URL = 'https://github.com/Usio-Energy/ENSEK'
EMAIL = 'richard@richard.do'
AUTHOR = 'Richard O\'Dwyer'
REQUIRES_PYTHON = '>=3.6.0'

here = os.path.abspath(os.path.dirname(__file__))
with io.open(os.path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    REQUIRED = f.read().splitlines()

with io.open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = '\n' + f.read()

setup(
    name=NAME,
    version='1.3.0',
    description=DESCRIPTION,
    long_description=long_description,
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages(exclude=('tests',)),
    install_requires=REQUIRED,
    include_package_data=True,
    license='Apache 2',
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
)
