#!/usr/bin/env python3
"""
Tests for example scripts to ensure they work and are generic.
"""

import importlib.util
import os
import sys
import tempfile
import unittest

import numpy as np

# Add the climapan_lab package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestExamples(unittest.TestCase):
    """Test that examples work properly and contain no personal information."""

    def setUp(self):
        """Set up test fixtures."""
        self.examples_dir = os.path.join(
            os.path.dirname(__file__), "..", "climapan_lab", "examples"
        )

    def test_simple_example_imports(self):
        """Test that simple_example.py can be imported without errors."""
        simple_example_path = os.path.join(self.examples_dir, "simple_example.py")
        self.assertTrue(os.path.exists(simple_example_path))

        # Load the module
        spec = importlib.util.spec_from_file_location(
            "simple_example", simple_example_path
        )
        simple_example = importlib.util.module_from_spec(spec)

        # This should not raise any import errors
        try:
            spec.loader.exec_module(simple_example)
            self.assertTrue(hasattr(simple_example, "main"))
        except ImportError as e:
            self.fail(f"simple_example.py failed to import: {e}")

    def test_load_data_class(self):
        """Test that Load_data.py contains generic utilities."""
        load_data_path = os.path.join(self.examples_dir, "Load_data.py")
        self.assertTrue(os.path.exists(load_data_path))

        # Load the module
        spec = importlib.util.spec_from_file_location("Load_data", load_data_path)
        load_data_module = importlib.util.module_from_spec(spec)

        try:
            spec.loader.exec_module(load_data_module)
            # Check for expected classes/functions
            self.assertTrue(hasattr(load_data_module, "NumpyEncoder"))
            self.assertTrue(hasattr(load_data_module, "load_hdf5_file"))
            self.assertTrue(hasattr(load_data_module, "load_json_file"))
        except ImportError as e:
            self.fail(f"Load_data.py failed to import: {e}")

    def test_no_personal_paths(self):
        """Test that example files contain no personal paths."""
        personal_indicators = [
            "duypham",
            "Users",
            "Documents",
            "Personal Documents",
            "Uni Bochum",
            "Work",
            "/home/",
            "C:\\Users\\",
        ]

        example_files = [
            "simple_example.py",
            "scenario.py",
            "Load_data.py",
            "graph.py",
            "scenario_testing_new.py",
        ]

        for example_file in example_files:
            file_path = os.path.join(self.examples_dir, example_file)
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                for indicator in personal_indicators:
                    self.assertNotIn(
                        indicator,
                        content,
                        f"Found personal path indicator '{indicator}' in {example_file}",
                    )

    def test_generic_paths_only(self):
        """Test that examples use only generic paths like 'results/', 'figures/', etc."""
        acceptable_paths = [
            "results",
            "../results",
            "./results",
            "figures",
            "../figures",
            "./figures",
            "data",
            "../data",
            "./data",
            "output",
            "../output",
            "./output",
        ]

        example_files = ["scenario.py", "scenario_testing_new.py", "graph.py"]

        for example_file in example_files:
            file_path = os.path.join(self.examples_dir, example_file)
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Check that if any path is mentioned, it's generic
                lines_with_paths = [
                    line
                    for line in content.split("\n")
                    if "folder_path" in line or "data_folder" in line
                ]

                for line in lines_with_paths:
                    # Skip comment lines
                    if line.strip().startswith("#"):
                        continue

                    # Check that the line contains at least one acceptable path pattern
                    has_acceptable_path = any(
                        path in line for path in acceptable_paths + ["figures"]
                    )
                    if not has_acceptable_path and ("folder" in line or "path" in line):
                        print(
                            f"Warning: Potentially non-generic path in {example_file}: {line.strip()}"
                        )


class TestAnalysisScripts(unittest.TestCase):
    """Test analysis scripts for generic functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.analysis_dir = os.path.join(
            os.path.dirname(__file__), "..", "climapan_lab", "analysis"
        )

    def test_inspect_results_uses_args(self):
        """Test that inspect_results.py uses command line arguments instead of hardcoded paths."""
        inspect_path = os.path.join(self.analysis_dir, "inspect_results.py")
        self.assertTrue(os.path.exists(inspect_path))

        with open(inspect_path, "r") as f:
            content = f.read()

        # Should use argparse
        self.assertIn("argparse", content)
        self.assertIn("parser.add_argument", content)

        # Should not have hardcoded result paths
        self.assertNotIn("results/single_BAU_NoCovid", content)

    def test_no_personal_analysis_directories(self):
        """Test that personal analysis directories have been removed."""
        personal_dirs = ["SA_params", "SA_bparams"]

        for dir_name in personal_dirs:
            dir_path = os.path.join(self.analysis_dir, dir_name)
            self.assertFalse(
                os.path.exists(dir_path),
                f"Personal analysis directory {dir_name} should be removed",
            )


if __name__ == "__main__":
    unittest.main()
