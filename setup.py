#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

import unittest
from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['xarray', 'numpy']

setup_requirements = [ ]

test_requirements = [ ]

setup(
    author="Eviatar Bach",
    author_email='eviatarbach@protonmail.com',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    description="Utility for facilitating parallel parameter sweeps.",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='parasweep',
    name='parasweep',
    packages=find_packages(include=['parasweep']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/eviatarbach/parasweep',
    version='2019.01',
    zip_safe=False,
)
