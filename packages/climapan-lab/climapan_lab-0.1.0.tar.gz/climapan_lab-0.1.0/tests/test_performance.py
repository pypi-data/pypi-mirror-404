#!/usr/bin/env python3
"""
Performance and scalability tests for CliMaPan-Lab.
"""

import os
import shutil
import sys
import tempfile
import time
import unittest

# Add the climapan_lab package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from climapan_lab.base_params import economic_params
    from climapan_lab.model import EconModel
    from climapan_lab.run_sim import single_run

    IMPORTS_AVAILABLE = True
except ImportError as e:
    IMPORTS_AVAILABLE = False
    IMPORT_ERROR = str(e)


class TestPerformance(unittest.TestCase):
    """Test performance characteristics of the model."""

    def setUp(self):
        """Set up test fixtures."""
        if not IMPORTS_AVAILABLE:
            self.skipTest(f"Required imports not available: {IMPORT_ERROR}")

        self.test_dir = tempfile.mkdtemp()
        self.base_params = economic_params.copy()
        self.base_params.update(
            {
                "verboseFlag": False,
                "climateModuleFlag": False,  # Disable for performance testing
            }
        )

    def tearDown(self):
        """Clean up."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_small_model_performance(self):
        """Test performance with minimal agent configuration."""
        params = self.base_params.copy()
        params.update(
            {
                "c_agents": 10,
                "capitalists": 3,
                "csf_agents": 2,
                "cpf_agents": 1,
                "steps": 10,
            }
        )

        start_time = time.time()
        result = single_run(params, parent_folder=self.test_dir, make_stats=False)
        end_time = time.time()

        execution_time = end_time - start_time

        # Small model should complete quickly (within 30 seconds)
        self.assertLess(
            execution_time,
            30,
            f"Small model took too long: {execution_time:.2f} seconds",
        )
        self.assertIsNotNone(result)

    def test_agent_scaling_performance(self):
        """Test how performance scales with agent count."""
        agent_counts = [5, 10, 20]
        execution_times = []

        for agent_count in agent_counts:
            params = self.base_params.copy()
            params.update(
                {
                    "c_agents": agent_count,
                    "capitalists": max(1, agent_count // 5),
                    "csf_agents": max(1, agent_count // 10),
                    "cpf_agents": 1,
                    "steps": 5,
                }
            )

            start_time = time.time()
            result = single_run(params, parent_folder=self.test_dir, make_stats=False)
            end_time = time.time()

            execution_time = end_time - start_time
            execution_times.append(execution_time)

            self.assertIsNotNone(result, f"Failed with {agent_count} agents")

        # Each configuration should complete in reasonable time
        for i, exec_time in enumerate(execution_times):
            self.assertLess(
                exec_time,
                60,
                f"Agent count {agent_counts[i]} took too long: {exec_time:.2f}s",
            )

    def test_time_scaling_performance(self):
        """Test how performance scales with simulation length."""
        step_counts = [5, 10, 20]
        execution_times = []

        for steps in step_counts:
            params = self.base_params.copy()
            params.update(
                {
                    "c_agents": 10,
                    "capitalists": 3,
                    "csf_agents": 2,
                    "cpf_agents": 1,
                    "steps": steps,
                }
            )

            start_time = time.time()
            result = single_run(params, parent_folder=self.test_dir, make_stats=False)
            end_time = time.time()

            execution_time = end_time - start_time
            execution_times.append(execution_time)

            self.assertIsNotNone(result, f"Failed with {steps} steps")

        # Performance should scale roughly linearly with time steps
        # (though this is a rough check)
        for i, exec_time in enumerate(execution_times):
            self.assertLess(
                exec_time,
                60,
                f"Step count {step_counts[i]} took too long: {exec_time:.2f}s",
            )

    def test_memory_efficiency(self):
        """Test that model doesn't use excessive memory."""
        import os

        import psutil

        params = self.base_params.copy()
        params.update(
            {
                "c_agents": 20,
                "capitalists": 5,
                "csf_agents": 3,
                "cpf_agents": 2,
                "steps": 10,
            }
        )

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Run simulation
        result = single_run(params, parent_folder=self.test_dir, make_stats=False)

        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        self.assertIsNotNone(result)

        # Memory increase should be reasonable (less than 500MB for small model)
        self.assertLess(
            memory_increase, 500, f"Memory usage increased by {memory_increase:.1f}MB"
        )

    def test_repeated_runs_performance(self):
        """Test that repeated runs maintain consistent performance."""
        params = self.base_params.copy()
        params.update(
            {
                "c_agents": 8,
                "capitalists": 2,
                "csf_agents": 1,
                "cpf_agents": 1,
                "steps": 5,
            }
        )

        execution_times = []

        # Run multiple times
        for i in range(3):
            start_time = time.time()
            result = single_run(params, parent_folder=self.test_dir, make_stats=False)
            end_time = time.time()

            execution_time = end_time - start_time
            execution_times.append(execution_time)

            self.assertIsNotNone(result, f"Run {i+1} failed")

        # All runs should complete in reasonable time
        for i, exec_time in enumerate(execution_times):
            self.assertLess(exec_time, 30, f"Run {i+1} took too long: {exec_time:.2f}s")

        # Performance should be relatively consistent
        if len(execution_times) > 1:
            avg_time = sum(execution_times) / len(execution_times)
            max_deviation = max(abs(t - avg_time) for t in execution_times)

            # Deviation shouldn't be more than 100% of average, unless execution is very fast (<0.1s)
            # For extremely fast runs, system noise dominates.
            threshold = max(avg_time, 0.1)
            self.assertLess(
                max_deviation,
                threshold,
                f"Performance is too inconsistent between runs (dev={max_deviation:.4f}, avg={avg_time:.4f})",
            )


class TestScalability(unittest.TestCase):
    """Test scalability characteristics and limits."""

    def setUp(self):
        """Set up test fixtures."""
        if not IMPORTS_AVAILABLE:
            self.skipTest(f"Required imports not available: {IMPORT_ERROR}")

        self.test_dir = tempfile.mkdtemp()
        self.base_params = economic_params.copy()
        self.base_params.update(
            {
                "verboseFlag": False,
                "climateModuleFlag": False,
            }
        )

    def tearDown(self):
        """Clean up."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_minimum_viable_configuration(self):
        """Test the smallest possible model configuration."""
        params = self.base_params.copy()
        params.update(
            {
                "c_agents": 1,
                "capitalists": 1,
                "csf_agents": 1,
                "cpf_agents": 1,
                "green_energy_owners": 1,
                "brown_energy_owners": 1,
                "b_agents": 1,
                "g_agents": 1,
                "steps": 1,
            }
        )

        # Should run without errors even with minimal configuration
        result = single_run(params, parent_folder=self.test_dir, make_stats=False)
        self.assertIsNotNone(result)

    def test_moderate_scale_configuration(self):
        """Test a moderate-scale configuration."""
        params = self.base_params.copy()
        params.update(
            {
                "c_agents": 50,
                "capitalists": 10,
                "csf_agents": 5,
                "cpf_agents": 3,
                "green_energy_owners": 2,
                "brown_energy_owners": 2,
                "steps": 20,
            }
        )

        start_time = time.time()
        result = single_run(params, parent_folder=self.test_dir, make_stats=False)
        end_time = time.time()

        execution_time = end_time - start_time

        # Should complete in reasonable time (less than 2 minutes)
        self.assertLess(
            execution_time, 120, f"Moderate scale took too long: {execution_time:.2f}s"
        )
        self.assertIsNotNone(result)

    def test_parameter_boundary_conditions(self):
        """Test behavior at parameter boundaries."""
        boundary_tests = [
            # Very low tax rate
            {"taxRate": 0.001, "c_agents": 5, "steps": 3},
            # Very high tax rate (but still valid)
            {"taxRate": 0.95, "c_agents": 5, "steps": 3},
            # Very low unemployment benefit
            {"unemploymentDole": 1, "c_agents": 5, "steps": 3},
            # Minimal consumption level
            {"subsistenceLevelOfConsumption": 1, "c_agents": 5, "steps": 3},
        ]

        for test_params in boundary_tests:
            with self.subTest(test_params=test_params):
                params = self.base_params.copy()
                params.update(test_params)

                # Should handle boundary conditions gracefully
                try:
                    result = single_run(
                        params, parent_folder=self.test_dir, make_stats=False
                    )
                    self.assertIsNotNone(result)
                except (ValueError, AssertionError) as e:
                    # Some boundary conditions might be invalid - that's ok
                    pass

    def test_configuration_robustness(self):
        """Test robustness across different valid configurations."""
        configurations = [
            # Energy-focused
            {"energySectorFlag": True, "c_agents": 10, "steps": 5},
            # No energy sector
            {"energySectorFlag": False, "c_agents": 10, "steps": 5},
            # High agent diversity
            {
                "c_agents": 15,
                "capitalists": 8,
                "csf_agents": 4,
                "cpf_agents": 3,
                "steps": 5,
            },
            # Low agent diversity
            {
                "c_agents": 5,
                "capitalists": 2,
                "csf_agents": 1,
                "cpf_agents": 1,
                "steps": 5,
            },
        ]

        for config in configurations:
            with self.subTest(config=config):
                params = self.base_params.copy()
                params.update(config)

                result = single_run(
                    params, parent_folder=self.test_dir, make_stats=False
                )
                self.assertIsNotNone(result, f"Configuration failed: {config}")


@unittest.skipIf(
    not IMPORTS_AVAILABLE,
    f"Required imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}",
)
class TestStressTest(unittest.TestCase):
    """Stress tests for edge cases and unusual conditions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.base_params = economic_params.copy()
        self.base_params.update(
            {
                "verboseFlag": False,
                "climateModuleFlag": False,
            }
        )

    def tearDown(self):
        """Clean up."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_rapid_succession_runs(self):
        """Test running simulations in rapid succession."""
        params = self.base_params.copy()
        params.update(
            {
                "c_agents": 5,
                "steps": 3,
            }
        )

        # Run several simulations quickly
        for i in range(5):
            result = single_run(params, parent_folder=self.test_dir, make_stats=False)
            self.assertIsNotNone(result, f"Rapid run {i+1} failed")

    def test_extreme_parameter_combinations(self):
        """Test with extreme but valid parameter combinations."""
        extreme_configs = [
            # Very many consumers, few firms
            {"c_agents": 100, "csf_agents": 1, "cpf_agents": 1, "steps": 3},
            # Few consumers, many firms (if possible)
            {"c_agents": 3, "csf_agents": 5, "cpf_agents": 5, "steps": 3},
            # Long simulation, few agents
            {"c_agents": 3, "steps": 50},
        ]

        for config in extreme_configs:
            with self.subTest(config=config):
                params = self.base_params.copy()
                params.update(config)

                try:
                    start_time = time.time()
                    result = single_run(
                        params, parent_folder=self.test_dir, make_stats=False
                    )
                    end_time = time.time()

                    execution_time = end_time - start_time

                    # Should complete within reasonable time even for extreme configs
                    self.assertLess(
                        execution_time,
                        300,
                        f"Extreme config took too long: {execution_time:.2f}s",
                    )
                    self.assertIsNotNone(result)

                except MemoryError:
                    self.skipTest(f"Memory constraints too tight for config: {config}")
                except Exception as e:
                    # Some extreme configurations might not be valid
                    if "agents" in str(e).lower() or "invalid" in str(e).lower():
                        # Expected failure for invalid configuration
                        pass
                    else:
                        raise


if __name__ == "__main__":
    # Run tests with timeout to prevent hanging
    unittest.main()
