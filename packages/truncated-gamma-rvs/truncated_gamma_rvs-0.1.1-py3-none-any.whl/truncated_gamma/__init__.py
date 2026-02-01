"""
Truncated Gamma Random Variates Package

A Python package to generate random variates from a truncated gamma distribution.
"""

from .truncated_gamma import TruncatedGamma, truncgamma_rvs

__version__ = "0.1.1"
__author__ = "Wade K. Copeland"
__email__ = "wade@kingcopeland.com"

# This controls what gets imported with "from truncated_gamma import *"
__all__ = ["TruncatedGamma", "truncgamma_rvs"]
