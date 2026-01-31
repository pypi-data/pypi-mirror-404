import argparse
import importlib.util
import json
import multiprocessing
import os
import shutil
from multiprocessing import Pool

import numpy as np
import sobol_seq
from src.models import EconModel
from tqdm import tqdm


# Utility functions
def serialize_value(value):
    """Convert value to a JSON-compatible format."""
    if isinstance(value, (int, float, str, bool, type(None))):
        return value
    elif isinstance(value, np.integer):
        return int(value)
    elif isinstance(value, np.floating):
        return float(value)
    elif isinstance(value, np.ndarray):
        return value.tolist()
    elif isinstance(value, list):
        return [serialize_value(v) for v in value]
    elif isinstance(value, dict):
        return {k: serialize_value(v) for k, v in value.items()}
    else:
        return str(value)


def load_python_file(file_path):
    """Load a Python file and return its module."""
    spec = importlib.util.spec_from_file_location("module", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Custom JSON encoder for handling Numpy data types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, bytes):
            return obj.decode("utf-8")
        elif isinstance(obj, (complex, np.complex128)):
            return [obj.real, obj.imag]
        elif isinstance(obj, (set, frozenset)):
            return list(obj)
        elif hasattr(obj, "tolist"):
            return obj.tolist()
        elif hasattr(obj, "__dict__"):
            return {key: self.default(value) for key, value in obj.__dict__.items()}
        return super(NumpyEncoder, self).default(obj)


class SensitivityAnalyzer:
    def __init__(
        self,
        save_path,
        base_params_file,
        sensitivity_params_file,
        num_workers=None,
        budget=500,
        varlist_path="varlist.txt",
        num_seeds=50,
    ):
        self.save_path = os.path.abspath(save_path)  # Use absolute paths
        self.budget = budget
        self.num_workers = (
            num_workers if num_workers is not None else multiprocessing.cpu_count()
        )
        self.varlist_path = os.path.abspath(varlist_path)
        self.varlist = self._load_varlist()
        self.base_params_file = base_params_file
        self.sensitivity_params_file = sensitivity_params_file
        self.base_params = self._load_base_params()
        self.sensitivity_params = self._load_sensitivity_params()
        self.num_seeds = num_seeds

        # Fix the upper bound to avoid int32 overflow
        self.seeds = np.random.randint(0, 2**31 - 1, size=self.num_seeds)

        self.params_keys = list(self.sensitivity_params.keys())
        self.exploration_range = np.array(
            [self.sensitivity_params[k] for k in self.params_keys]
        )
        self.n_dims = self.exploration_range.shape[0]
        self._prep_params_variations()

        self.experiment_folder = self._create_experiment_folder()

    def _generate_filename(self):
        param_string = "_".join([f"{key}" for key in self.params_keys])
        return f"sensitivity_analysis_{param_string}_b{self.budget}_s{self.num_seeds}"

    def _create_experiment_folder(self):
        experiment_name = self._generate_filename()
        experiment_path = os.path.join(self.save_path, experiment_name)
        os.makedirs(experiment_path, exist_ok=True)
        return experiment_path

    def _load_varlist(self):
        with open(self.varlist_path, "r") as f:
            return [line.strip() for line in f if line.strip()]

    def _load_base_params(self):
        module = load_python_file(self.base_params_file)
        return module.parameters

    def _load_sensitivity_params(self):
        module = load_python_file(self.sensitivity_params_file)
        return module.params

    def _prep_params_variations(self):
        self.input_batch = self._get_sobol_samples(
            self.n_dims, self.budget, self.exploration_range
        )

    def _get_sobol_samples(self, n_dims, samples, parameter_support):
        support_range = parameter_support[:, 1] - parameter_support[:, 0]
        random_samples = sobol_seq.i4_sobol_generate(n_dims, samples)
        sobol_samples = (
            np.multiply(random_samples, support_range) + parameter_support[:, 0]
        )
        return sobol_samples

    def _run_sim(self, params_combination, seed):
        # Start with base parameters
        parameters = self.base_params.copy()

        # Update with sensitivity parameters
        for i, key in enumerate(self.params_keys):
            if key in [
                "c_agents",
                "capitalists",
                "green_energy_owners",
                "brown_energy_owners",
                "b_agents",
                "csf_agents",
                "cpf_agents",
            ]:
                parameters[key] = int(params_combination[i])
            else:
                if key == "unemploymentDole":
                    parameters["subsistenceLevelOfConsumption"] = params_combination[i]
                parameters[key] = params_combination[i]

        # Set the random seed
        np.random.seed(seed)

        model = EconModel(parameters)
        parameters["seed"] = seed
        results = model.run()

        output = {}
        for var in self.varlist:
            if var in results.variables.EconModel:
                output[var] = results.variables.EconModel[var]

        # Combine input parameters, seed, and output
        return {**parameters, "seed": seed, **output}

    def _process_sample(self, args):
        batch_idx, params_combination = args
        results = []
        for seed in self.seeds:
            result = self._run_sim(params_combination, seed)
            result["batch_idx"] = batch_idx
            results.append(result)
        return results

    def _process_batch(self):
        total_simulations = self.budget * self.num_seeds
        with tqdm(
            total=total_simulations, desc="Processing samples", unit="simulation"
        ) as pbar:
            with Pool(processes=self.num_workers) as pool:
                for results in pool.imap_unordered(
                    self._process_sample, enumerate(self.input_batch)
                ):
                    self._save_results(results)
                    pbar.update(len(results))

    def _save_results(self, results):
        for result in results:
            batch_idx = result["batch_idx"]
            seed = result["seed"]

            # Create batch directory within the experiment folder
            batch_dir = os.path.join(self.experiment_folder, f"batch_{batch_idx:04d}")
            os.makedirs(batch_dir, exist_ok=True)

            # Save result to JSON file
            filename = f"seed_{seed:010d}.json"
            file_path = os.path.join(batch_dir, filename)
            with open(file_path, "w") as f:
                json.dump(result, f, cls=NumpyEncoder, indent=2)

    def _zip_results(self):
        zip_filename = f"{os.path.basename(self.experiment_folder)}.zip"
        shutil.make_archive(
            os.path.join(self.save_path, os.path.basename(self.experiment_folder)),
            "zip",
            self.experiment_folder,
        )
        print(f"Results zipped to {zip_filename}")

    def analyze(self):
        print(
            f"Starting sensitivity analysis with {self.budget} parameter combinations and {self.num_seeds} seeds each..."
        )
        print(f"Results will be saved in {self.experiment_folder}")
        self._process_batch()
        print(f"Processing complete. Results saved in {self.experiment_folder}")
        self._zip_results()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-b",
        "--budget",
        type=int,
        default=1000,
        help="number of parameter combinations",
    )
    parser.add_argument(
        "-s", "--save_path", type=str, required=True, help="path to save results"
    )
    parser.add_argument(
        "-w", "--num_workers", type=int, default=None, help="number of parallel workers"
    )
    parser.add_argument(
        "-v",
        "--varlist",
        type=str,
        default="varlist.txt",
        help="path to the variable list file",
    )
    parser.add_argument(
        "-p",
        "--sensitivity_params",
        type=str,
        required=True,
        help="path to the sensitivity parameters Python file",
    )
    parser.add_argument(
        "-bp",
        "--base_params",
        type=str,
        required=True,
        help="path to the base parameters Python file",
    )
    parser.add_argument(
        "-n",
        "--num_seeds",
        type=int,
        default=50,
        help="number of random seeds to use for each parameter combination",
    )
    args = parser.parse_args()

    analyzer = SensitivityAnalyzer(
        save_path=args.save_path,
        base_params_file=args.base_params,
        sensitivity_params_file=args.sensitivity_params,
        budget=args.budget,
        num_workers=args.num_workers,
        varlist_path=args.varlist,
        num_seeds=args.num_seeds,
    )
    analyzer.analyze()

    print("Comprehensive sensitivity analysis completed.")
