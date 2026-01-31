#!/usr/bin/env python3
"""
Basic functionality tests for CliMaPan-Lab.
"""

import os
import sys
import tempfile
import unittest

import numpy as np

# Add the climapan_lab package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from climapan_lab.base_params import economic_params
from climapan_lab.model import EconModel
from climapan_lab.src.consumers.Consumer import Consumer
from climapan_lab.src.firms.CapitalGoodsFirm import CapitalGoodsFirm
from climapan_lab.src.firms.ConsumerGoodsFirm import ConsumerGoodsFirm


class TestBasicFunctionality(unittest.TestCase):
    """Test basic functionality of the economic model."""

    def setUp(self):
        """Set up test fixtures."""
        self.params = economic_params.copy()
        # Use small numbers for testing
        self.params.update(
            {
                "c_agents": 10,
                "capitalists": 3,
                "csf_agents": 2,
                "cpf_agents": 2,  # Need at least 2 for energy type diversity
                "steps": 5,
                "verboseFlag": False,
                "climateModuleFlag": False,  # Disable for faster testing
                "covid_settings": None,  # Disable COVID for testing
            }
        )

    def test_model_creation(self):
        """Test that we can create a model instance."""
        model = EconModel(self.params)
        self.assertIsInstance(model, EconModel)
        # Model needs to be set up before agents are created
        model.setup()
        self.assertEqual(len(model.consumer_agents), self.params["c_agents"])

    def test_model_step(self):
        """Test that we can run a single step of the model."""
        model = EconModel(self.params)
        model.setup()
        # Test that step() executes without error
        try:
            model.step()
            step_completed = True
        except Exception:
            step_completed = False
        self.assertTrue(step_completed, "Model step should complete without error")

    def test_agent_creation(self):
        """Test that agents can be created with proper attributes."""
        model = EconModel(self.params)
        model.setup()

        # Test consumer creation
        consumer = model.consumer_agents[0]
        self.assertIsInstance(consumer, Consumer)
        self.assertTrue(hasattr(consumer, "deposit"))

        # Test firm creation
        if len(model.csfirm_agents) > 0:
            firm = model.csfirm_agents[0]
            self.assertIsInstance(firm, ConsumerGoodsFirm)
            self.assertTrue(hasattr(firm, "netWorth"))

    def test_parameters_validation(self):
        """Test that parameters can be loaded and models created."""
        # Test that model creation with valid parameters works
        model = EconModel(self.params)
        self.assertIsInstance(model, EconModel)

        # Test that model can access parameters
        self.assertTrue(hasattr(model, "p"))
        self.assertEqual(model.p.c_agents, self.params["c_agents"])

    def test_model_run_short(self):
        """Test that we can run the model for a few steps."""

    def test_model_run_short(self):
        """Test that we can run the model for a few steps."""
        model = EconModel(self.params)
        results = model.run()

        # Check that the model ran for the expected number of steps
        self.assertEqual(model.t, self.params["steps"])

        # Check that data collection works (ambr returns dict with 'model' DataFrame)
        # Legacy AgentPy checked model.output.variables
        # We now check the returned results
        if isinstance(results, dict):
            self.assertIn("model", results)
            self.assertFalse(results["model"].is_empty())
        else:
            # If wrapper is used or AgentPy compat matches
            self.assertTrue(hasattr(results, "variables"))
            self.assertTrue(hasattr(results.variables, "EconModel"))


class TestDataStructures(unittest.TestCase):
    """Test data structures and utilities."""

    def test_parameter_structure(self):
        """Test that economic parameters have expected structure."""
        params = economic_params

        # Check for essential parameters
        essential_keys = [
            "c_agents",
            "steps",
            "taxRate",
            "unemploymentDole",
            "subsistenceLevelOfConsumption",
        ]

        for key in essential_keys:
            self.assertIn(key, params, f"Missing essential parameter: {key}")

    def test_numpy_compatibility(self):
        """Test that the package works with numpy arrays."""
        test_array = np.array([1, 2, 3, 4, 5])
        self.assertEqual(len(test_array), 5)
        self.assertEqual(test_array.sum(), 15)


if __name__ == "__main__":
    unittest.main()
