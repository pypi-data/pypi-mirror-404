"""
CliMaPan-Lab: Climate-Pandemic Economic Modeling Laboratory

A comprehensive agent-based economic modeling framework that integrates
climate change and pandemic dynamics.
"""

__version__ = "0.1.0"
__author__ = "CliMaPan-Lab Team"
__email__ = "anh-duy.pham@uni-wuerzburg.de"

# Import main components for easy access
try:
    from .base_params import economic_params
    from .model import EconModel

    __all__ = ["EconModel", "economic_params"]
except ImportError:
    # Handle case where dependencies are not yet installed
    __all__ = []
