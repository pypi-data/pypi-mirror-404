import json
import os

import h5py
import numpy as np


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)


class NumpyDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, dct):
        for key, value in dct.items():
            if isinstance(value, list):
                try:
                    dct[key] = np.array(value)
                except:
                    pass
        return dct


def load_hdf5_file(file_path):
    """
    Load an HDF5 file and return its contents as a dictionary.
    """
    data = {}
    with h5py.File(file_path, "r") as f:
        for key in f.keys():
            value = f[key][()]
            if isinstance(value, np.ndarray) and value.dtype.kind == "S":
                # Convert byte strings to unicode
                value = value.astype(str)
            elif isinstance(value, np.ndarray) and value.shape == ():
                # Convert 0-dimensional arrays to scalars
                value = value.item()
            data[key] = value
    return data


def load_json_file(file_path):
    """
    Load a JSON file and return its contents as a dictionary.
    """
    with open(file_path, "r") as f:
        data = json.load(f, cls=NumpyDecoder)
    return data


def load_experiment_results(experiment_folder):
    """
    Load all results from an experiment folder.
    """
    all_results = []
    for batch_folder in sorted(os.listdir(experiment_folder)):
        batch_path = os.path.join(experiment_folder, batch_folder)
        if os.path.isdir(batch_path):
            for seed_file in sorted(os.listdir(batch_path)):
                if seed_file.endswith(".h5"):
                    file_path = os.path.join(batch_path, seed_file)
                    result = load_hdf5_file(file_path)
                    all_results.append(result)
                elif seed_file.endswith(".json"):
                    file_path = os.path.join(batch_path, seed_file)
                    result = load_json_file(file_path)
                    all_results.append(result)
    return all_results
