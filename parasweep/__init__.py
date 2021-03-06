# -*- coding: utf-8 -*-

"""Top-level package for parasweep."""

__author__ = """Eviatar Bach"""
__email__ = 'eviatarbach@protonmail.com'
__version__ = '2020.10'

from parasweep.sweep import run_sweep
from parasweep.sweepers import CartesianSweep, FilteredCartesianSweep, \
                               SetSweep, RandomSweep
