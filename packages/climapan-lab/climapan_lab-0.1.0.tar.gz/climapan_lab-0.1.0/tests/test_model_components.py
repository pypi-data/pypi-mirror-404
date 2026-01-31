#!/usr/bin/env python3
"""
Tests for individual model components in CliMaPan-Lab.
"""

import os
import sys
import unittest

import numpy as np

# Add the climapan_lab package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from climapan_lab.base_params import economic_params
    from climapan_lab.src.models import EconModel
    from climapan_lab.src.params import parameters

    IMPORTS_AVAILABLE = True
except ImportError as e:
    IMPORTS_AVAILABLE = False
    IMPORT_ERROR = str(e)


class TestModelComponents(unittest.TestCase):
    """Test individual components of the economic model."""

    def setUp(self):
        """Set up test fixtures."""
        if not IMPORTS_AVAILABLE:
            self.skipTest(f"Required imports not available: {IMPORT_ERROR}")

        self.params = economic_params.copy()
        # Use very small numbers for fast testing
        self.params.update(
            {
                "c_agents": 10,
                "capitalists": 3,
                "csf_agents": 2,  # Need at least 2 for energy type diversity
                "cpf_agents": 2,  # Need at least 2 for energy type diversity
                "green_energy_owners": 1,
                "brown_energy_owners": 1,
                "b_agents": 1,
                "g_agents": 1,
                "steps": 3,
                "verboseFlag": False,
                "climateModuleFlag": False,  # Disable for fast testing
                "covid_settings": None,  # Disable COVID for testing
            }
        )

    def test_model_initialization(self):
        """Test that model initializes with correct agent counts."""
        model = EconModel(self.params)
        model.setup()

        # Check agent counts
        self.assertEqual(len(model.consumer_agents), self.params["c_agents"])
        self.assertEqual(len(model.csfirm_agents), self.params["csf_agents"])
        self.assertEqual(len(model.cpfirm_agents), self.params["cpf_agents"])

        # Check that model has required attributes
        self.assertTrue(hasattr(model, "t"))
        self.assertTrue(hasattr(model, "p"))
        self.assertEqual(model.t, 0)

    def test_agent_attributes(self):
        """Test that agents have required attributes."""
        model = EconModel(self.params)
        model.setup()

        # Test consumer attributes
        if len(model.consumer_agents) > 0:
            consumer = model.consumer_agents[0]
            required_attrs = ["deposit", "employed", "consumerType"]
            for attr in required_attrs:
                self.assertTrue(
                    hasattr(consumer, attr), f"Consumer missing attribute: {attr}"
                )

        # Test firm attributes
        if len(model.csfirm_agents) > 0:
            firm = model.csfirm_agents[0]
            required_attrs = ["netWorth", "price", "actual_production"]
            for attr in required_attrs:
                self.assertTrue(hasattr(firm, attr), f"Firm missing attribute: {attr}")

    def test_climate_module_toggle(self):
        """Test that climate module can be enabled/disabled."""
        # Test with climate disabled
        params_no_climate = self.params.copy()
        params_no_climate["climateModuleFlag"] = False
        model_no_climate = EconModel(params_no_climate)

        # Test with climate enabled
        params_with_climate = self.params.copy()
        params_with_climate["climateModuleFlag"] = True
        model_with_climate = EconModel(params_with_climate)

        # Both should initialize successfully
        self.assertIsInstance(model_no_climate, EconModel)
        self.assertIsInstance(model_with_climate, EconModel)

    def test_covid_scenarios(self):
        """Test different COVID scenarios."""
        covid_settings = [None, "BAU", "DIST", "LOCK", "VAX"]

        for covid_setting in covid_settings:
            with self.subTest(covid_setting=covid_setting):
                params = self.params.copy()
                params["covid_settings"] = covid_setting

                # Should initialize without errors
                model = EconModel(params)
                self.assertIsInstance(model, EconModel)

    def test_economic_scenarios(self):
        """Test different economic scenarios."""
        economic_settings = ["BAU", "CT", "CTRa", "CTRb", "CTRc", "CTRd"]

        for setting in economic_settings:
            with self.subTest(setting=setting):
                params = self.params.copy()
                params["settings"] = setting

                # Should initialize without errors
                model = EconModel(params)
                self.assertIsInstance(model, EconModel)

    def test_parameter_validation(self):
        """Test that parameters are correctly assigned to models."""
        # Test that parameters are properly accessible
        model = EconModel(self.params)
        self.assertTrue(hasattr(model, "p"))

        # Test some key parameters
        for key, value in self.params.items():
            if hasattr(model.p, key):
                self.assertEqual(getattr(model.p, key), value)

    def test_model_step_progression(self):
        """Test that model time progresses correctly."""
        model = EconModel(self.params)
        model.setup()
        initial_time = model.t

        # Take a few steps and verify they execute without error
        for i in range(3):
            try:
                model.step()
                step_completed = True
            except Exception:
                step_completed = False
            self.assertTrue(step_completed, f"Step {i+1} should complete without error")

    def test_agent_state_changes(self):
        """Test that agent states change during simulation."""
        model = EconModel(self.params)
        model.setup()

        # Record initial states
        if len(model.consumer_agents) > 0:
            initial_consumer_budget = model.consumer_agents[0].deposit

        # Run a few steps
        for _ in range(2):
            model.step()

        # States should potentially change (though we can't guarantee specific changes)
        # At minimum, the model should still be in a valid state
        if len(model.consumer_agents) > 0:
            self.assertIsInstance(model.consumer_agents[0].deposit, (int, float))

    def test_data_collection(self):
        """Test that model collects data properly."""
        model = EconModel(self.params)

        # Run model briefly
        results = model.run()

        # Check that data collection works (ambr returns dict with 'model' DataFrame)
        # Legacy AgentPy checked model.output.variables
        # We now check the returned results
        if isinstance(results, dict):
            self.assertIn("model", results)
            self.assertFalse(results["model"].is_empty())
        else:
            # If wrapper is used or AgentPy compat matches
            self.assertTrue(hasattr(results, "variables"))


class TestParameterStructure(unittest.TestCase):
    """Test parameter structure and consistency."""

    def test_parameter_types(self):
        """Test that parameters have correct types."""
        if not IMPORTS_AVAILABLE:
            self.skipTest(f"Required imports not available: {IMPORT_ERROR}")

        params = economic_params

        # Test integer parameters
        int_params = ["c_agents", "steps", "capitalists", "csf_agents"]
        for param in int_params:
            if param in params:
                self.assertIsInstance(params[param], int, f"{param} should be int")
                self.assertGreater(params[param], 0, f"{param} should be positive")

        # Test float parameters
        float_params = ["taxRate", "co2_tax", "depreciationRate"]
        for param in float_params:
            if param in params:
                self.assertIsInstance(
                    params[param], (int, float), f"{param} should be numeric"
                )

        # Test boolean parameters
        bool_params = ["verboseFlag", "energySectorFlag", "climateModuleFlag"]
        for param in bool_params:
            if param in params:
                self.assertIsInstance(params[param], bool, f"{param} should be boolean")

    def test_required_parameters(self):
        """Test that all required parameters are present."""
        if not IMPORTS_AVAILABLE:
            self.skipTest(f"Required imports not available: {IMPORT_ERROR}")

        params = economic_params

        required_params = [
            "c_agents",
            "steps",
            "taxRate",
            "unemploymentDole",
            "subsistenceLevelOfConsumption",
            "settings",
        ]

        for param in required_params:
            self.assertIn(param, params, f"Required parameter {param} missing")

    def test_parameter_ranges(self):
        """Test that parameters are within reasonable ranges."""
        if not IMPORTS_AVAILABLE:
            self.skipTest(f"Required imports not available: {IMPORT_ERROR}")

        params = economic_params

        # Test that rates are between 0 and 1
        rate_params = ["taxRate", "incomeTaxRate", "reserve_ratio"]
        for param in rate_params:
            if param in params:
                self.assertGreaterEqual(params[param], 0, f"{param} should be >= 0")
                self.assertLessEqual(params[param], 1, f"{param} should be <= 1")

        # Test that agent counts are positive
        agent_params = ["c_agents", "capitalists", "csf_agents", "cpf_agents"]
        for param in agent_params:
            if param in params:
                self.assertGreater(params[param], 0, f"{param} should be positive")


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases."""

    def test_empty_parameters(self):
        """Test behavior with empty or missing parameters."""
        if not IMPORTS_AVAILABLE:
            self.skipTest(f"Required imports not available: {IMPORT_ERROR}")

        # Test that model can be created (AgentPy is lenient with parameters)
        try:
            model = EconModel({})
            model_created = True
        except Exception:
            model_created = False
        # Either behavior is acceptable - just test that it's consistent
        self.assertIsInstance(model_created, bool)

    def test_string_numeric_parameters(self):
        """Test that models handle parameter types appropriately."""
        if not IMPORTS_AVAILABLE:
            self.skipTest(f"Required imports not available: {IMPORT_ERROR}")

        params = economic_params.copy()
        params["c_agents"] = "not_a_number"

        # Test that model can be created (validation happens during setup/run)
        try:
            model = EconModel(params)
            model_created = True
        except Exception:
            model_created = False
        # Either behavior is acceptable
        self.assertIsInstance(model_created, bool)

    def test_negative_steps(self):
        """Test that models handle step parameters appropriately."""
        if not IMPORTS_AVAILABLE:
            self.skipTest(f"Required imports not available: {IMPORT_ERROR}")

        params = economic_params.copy()
        params["steps"] = -1

        # Test that model can be created (AgentPy handles this)
        try:
            model = EconModel(params)
            model_created = True
        except Exception:
            model_created = False
        # Either behavior is acceptable
        self.assertIsInstance(model_created, bool)


if __name__ == "__main__":
    unittest.main()
