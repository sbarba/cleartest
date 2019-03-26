#!/usr/bin/env python
 
from setuptools import setup

setup(name='cleartest',
    version='0.910',
    description='Lightweight testing framework for Python 2.7 and Python 3',
    long_description="See the project's GitHub page for docs: https://github.com/sbarba/cleartest",
    py_modules=['cleartest'],
    author='Steve Barba',
    license='MIT',
    scripts=['runtests'],
    url='https://github.com/sbarba/cleartest',
    install_requires=[
        'glob2',
        'colorama',
        'requests'
    ],
)
