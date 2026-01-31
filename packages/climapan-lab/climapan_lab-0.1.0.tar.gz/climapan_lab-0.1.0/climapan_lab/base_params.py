#!/usr/bin/env python3
"""
Base parameters for CliMaPan-Lab economic model.
This module exports the default economic parameters for the simulation.
"""

# Import the parameters from the src directory
from .src.params import parameters

# Export as economic_params for consistency with new naming
economic_params = parameters
