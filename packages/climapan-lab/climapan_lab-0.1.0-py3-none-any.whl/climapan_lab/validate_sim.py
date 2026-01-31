"""
CliMaPan-Lab: Climate-Pandemic Economic Modeling Laboratory
Model Validation Script

This script provides tools for validating the economic model against real-world data
using autocorrelation analysis and parameter calibration.
"""

import argparse
import warnings

import ambr as am
import numpy as np
import pandas as pd
import sobol_seq
import statsmodels.api as sm
from joblib import Parallel, delayed
from tqdm.contrib.concurrent import thread_map

warnings.filterwarnings("ignore")
from src.models import EconModel
from src.params import parameters
from validation_params import params


class Validator:
    period_dict = {"annually": 1, "quarterly": 3, "monthly": 12}

    def __init__(
        self,
        real_data_path,
        save_path,
        num_workers=None,
        budget=500,
        multi_var=False,
        period="annually",
    ):
        self.real_data_path = real_data_path  # path to real data csv file
        self.budget = budget
        self.multi_var = multi_var
        self.save_path = save_path.strip()
        self.num_workers = num_workers
        self.period = Validator.period_dict[period.strip()]

        # Load csv file
        self.real_df = pd.read_csv(self.real_data_path.strip())
        if "Unnamed: 0" in self.real_df.columns:
            self.real_df = self.real_df.drop(columns=["Unnamed: 0"])

        # Prepare real variables autocorrelation
        self._prep_real_autocorrelation()

        # Prepare all the paramters yielded from the parameter variations file
        self.params_keys = list(params.keys())
        self.exploration_range = np.array([params[k] for k in self.params_keys])
        self.n_dims = self.exploration_range.shape[0]
        self._prep_params_variations()

        del self.n_dims
        del self.exploration_range

    def _prep_real_autocorrelation(self):
        if not self.multi_var:
            self.ac = sm.tsa.acf(self.real_df[self.real_df.columns[0]], nlags=6)
            self.ac = [self.ac]
        else:
            self.ac = []
            for var in self.real_df.columns:
                self.ac.append(sm.tsa.acf(self.real_df[var].dropna(), nlags=6))

    def _prep_params_variations(self):
        self.input_batch = self._get_sobol_samples(
            self.n_dims, self.budget, self.exploration_range
        )

    def _get_sobol_samples(self, n_dims, samples, parameter_support):
        support_range = parameter_support[:, 1] - parameter_support[:, 0]

        random_samples = sobol_seq.i4_sobol_generate(n_dims, samples)

        sobol_samples = np.vstack(
            [
                np.multiply(s, support_range) + parameter_support[:, 0]
                for s in random_samples
            ]
        )

        return sobol_samples

    def _run_sim(self, params_combination):
        for i in range(len(params_combination)):
            if self.params_keys[i] in [
                "c_agents",
                "capitalists",
                "green_energy_owners",
                "brown_energy_owners",
                "b_agents",
                "csf_agents",
                "cpf_agents",
            ]:
                parameters[self.params_keys[i]] = int(params_combination[i])
            else:
                if self.params_keys[i] == "unemploymentDole":
                    parameters["subsistenceLevelOfConsumption"] = params_combination[i]
                parameters[self.params_keys[i]] = params_combination[i]

        model = EconModel(parameters)
        results = model.run()

        if not self.multi_var:
            sim_res = np.array(
                [
                    results.variables.EconModel[self.real_df.columns[0]][i]
                    for i in range(
                        50, len(results.variables.EconModel["BankDataWriter"])
                    )
                ]
            )
            if len(sim_res.shape) > 1:
                sim_res = np.sum(sim_res, axis=1)

            if self.period != 1:
                interval = len(sim_res) // self.period
                sim_rvals = []
                for i in range(interval - 1):
                    sim_rvals.append(
                        np.sum(sim_res[i * self.period : (i + 1) * self.period])
                    )

                sim_res = sim_rvals

            sim_res = [sim_res]
        else:
            sim_res = []
            for var in self.real_df.columns:
                res = np.array(
                    [
                        results.variables.EconModel[var].values[i]
                        for i in range(
                            50, len(results.variables.EconModel["BankDataWriter"])
                        )
                    ]
                )
                if len(res.shape) > 1:
                    res = np.sum(res, axis=1)

                if self.period != 1:
                    interval = len(res) // self.period
                    rvals = []
                    for i in range(interval - 1):
                        rvals.append(
                            np.sum(res[i * self.period : (i + 1) * self.period])
                        )

                    res = rvals

                sim_res.append(res)

        return sim_res

    def _measure_calibration(self, sim_res):
        loss = 0
        for i in range(len(sim_res)):
            cleaned_sim_res = np.array(
                [k for k in sim_res[i] if not np.isnan(k) and not np.isinf(k)]
            )
            try:
                sim_ac = sm.tsa.acf(cleaned_sim_res, nlags=6)
            except ValueError:
                return np.inf
            loss += np.mean((self.ac[i] - sim_ac) ** 2)

            print(self.ac[i], sim_ac, loss)
        return loss

    def _process_sample(self, batch_idx, params_combination):
        print("Processing batch no. ", batch_idx)
        sim_res = self._run_sim(params_combination)
        loss = self._measure_calibration(sim_res)
        with open(self.save_path, "a+") as file:
            file.write(
                str(batch_idx)
                + " "
                + np.array2string(params_combination)
                + " "
                + str(loss)
            )
            file.write("\n")
        print("Finished batch no. ", batch_idx)

    def _process_batch(self):
        if self.num_workers is None:
            Parallel(n_jobs=-1, prefer="processes")(
                [
                    delayed(self._process_sample)(idx, params)
                    for idx, params in enumerate(self.input_batch)
                ]
            )
        else:
            Parallel(n_jobs=self.num_workers, prefer="processes")(
                [
                    delayed(self._process_sample)(idx, params)
                    for idx, params in enumerate(self.input_batch)
                ]
            )

    def validate(self):
        self._process_batch()


class ValidatorAbs:

    def __init__(
        self, real_data_path, save_path, num_workers=None, budget=500, multi_var=False
    ):
        self.real_data_path = real_data_path  # path to real data csv file
        self.budget = budget
        self.multi_var = multi_var
        self.save_path = save_path.strip()
        self.num_workers = num_workers

        # Load csv file
        self.real_df = pd.read_csv(self.real_data_path.strip())
        self.real_df = self.real_df.drop(columns=["Unnamed: 0"])

        # Prepare real variables
        self._prep_real()

        # Prepare all the paramters yielded from the parameter variations file
        self.params_keys = list(params.keys())
        self.exploration_range = np.array([params[k] for k in self.params_keys])
        self.n_dims = self.exploration_range.shape[0]
        self._prep_params_variations()

        del self.n_dims
        del self.exploration_range

    def _prep_real(self):
        if not self.multi_var:
            self.real = self.real_df[self.real_df.columns[0]]
            self.real = [self.real]
        else:
            self.real = []
            for var in self.real_df.columns:
                if len(var) > 0:
                    self.real.append(self.real_df[var])

    def _prep_params_variations(self):
        self.input_batch = self._get_sobol_samples(
            self.n_dims, self.budget, self.exploration_range
        )

    def _get_sobol_samples(self, n_dims, samples, parameter_support):
        support_range = parameter_support[:, 1] - parameter_support[:, 0]

        random_samples = sobol_seq.i4_sobol_generate(n_dims, samples)

        sobol_samples = np.vstack(
            [
                np.multiply(s, support_range) + parameter_support[:, 0]
                for s in random_samples
            ]
        )

        return sobol_samples

    def _run_sim(self, params_combination):
        for i in range(len(params_combination)):
            if self.params_keys[i] in [
                "c_agents",
                "capitalists",
                "green_energy_owners",
                "brown_energy_owners",
                "b_agents",
                "csf_agents",
                "cpf_agents",
            ]:
                parameters[self.params_keys[i]] = int(params_combination[i])
            else:
                if self.params_keys[i] == "unemploymentDole":
                    parameters["subsistenceLevelOfConsumption"] = params_combination[i]
                parameters[self.params_keys[i]] = params_combination[i]

        model = EconModel(parameters)
        results = model.run()

        if not self.multi_var:
            start_date = int(parameters["start_date"].split("-")[0]) - 1
            pos = []
            for idx, i in enumerate(results.variables.EconModel["date"]):
                date = str(i).split("-")
                if (
                    int(date[2]) == 31
                    and int(date[1]) == 12
                    and int(date[0])
                    in [
                        start_date,
                        start_date + 10,
                        start_date + 20,
                        start_date + 30,
                        start_date + 40,
                        start_date + 50,
                        start_date + 60,
                        start_date + 70,
                        start_date + 80,
                        start_date + 90,
                        start_date + 100,
                    ]
                ):
                    pos.append(idx)
            print(pos)
            sim_res = np.array(
                [
                    results.variables.EconModel[self.real_df.columns[0]].values[i]
                    for i in range(len(results.variables.EconModel["BankDataWriter"]))
                    if i in pos
                ]
            )
            if len(sim_res.shape) > 1:
                sim_res = np.sum(sim_res, axis=1)

            # if self.period != 1:
            #     interval = len(sim_res) // self.period
            #     sim_rvals = []
            #     for i in range(interval-1):
            #         sim_rvals.append(np.sum(sim_res[i*self.period:(i+1)*self.period]))

            #     sim_res = sim_rvals

            sim_res = [sim_res]
        else:
            start_date = int(parameters["start_date"].split("-")[0]) - 1
            pos = []
            for idx, i in enumerate(results.variables.EconModel["date"]):
                date = str(i).split("-")
                if (
                    int(date[2]) == 31
                    and int(date[1]) == 12
                    and int(date[0])
                    in [
                        start_date,
                        start_date + 10,
                        start_date + 20,
                        start_date + 30,
                        start_date + 40,
                        start_date + 50,
                        start_date + 60,
                        start_date + 70,
                        start_date + 80,
                        start_date + 90,
                        start_date + 100,
                    ]
                ):
                    pos.append(idx)
            sim_res = []
            for var in self.real_df.columns:
                res = np.array(
                    [
                        results.variables.EconModel[var][i]
                        for i in range(
                            len(results.variables.EconModel["BankDataWriter"])
                        )
                        if i in pos
                    ]
                )
                if len(res.shape) > 1:
                    res = np.sum(res, axis=1)

                # if self.period != 1:
                #     interval = len(res) // self.period
                #     rvals = []
                #     for i in range(interval-1):
                #         rvals.append(np.sum(res[i*self.period:(i+1)*self.period]))

                #     res = rvals

                sim_res.append(res)

        return sim_res

    def _measure_calibration(self, sim_res):
        loss = 0
        for i in range(min(len(sim_res), len(self.real))):
            loss += np.sum(np.power((self.real[i] - sim_res[i] / 1e9), 2))

        return loss

    def _process_sample(self, batch_idx, params_combination):
        print("Processing batch no. ", batch_idx)
        sim_res = self._run_sim(params_combination)
        loss = self._measure_calibration(sim_res)
        with open(self.save_path, "a+") as file:
            file.write(
                str(batch_idx)
                + " "
                + np.array2string(params_combination)
                + " "
                + str(loss)
            )
            file.write("\n")
        print("Finished batch no. ", batch_idx)

    def _process_batch(self):
        if self.num_workers is None:
            Parallel(n_jobs=-1, prefer="processes")(
                [
                    delayed(self._process_sample)(idx, params)
                    for idx, params in enumerate(self.input_batch)
                ]
            )
        else:
            Parallel(n_jobs=self.num_workers, prefer="processes")(
                [
                    delayed(self._process_sample)(idx, params)
                    for idx, params in enumerate(self.input_batch)
                ]
            )

    def validate(self):
        self._process_batch()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--budget", type=int, default=1000, help="budget")
    parser.add_argument(
        "-f",
        "--real_path",
        type=str,
        default=None,
        required=True,
        help="real_data_path",
    )
    parser.add_argument(
        "-s", "--save_path", type=str, default=None, required=True, help="save_path"
    )
    parser.add_argument(
        "-m",
        "--multi_var",
        action="store_true",
        help="(bool) if real data has multi variables?",
    )
    parser.add_argument("-p", "--period", type=str, default="annually", help="period")
    parser.add_argument(
        "-a", "--ac", action="store_true", help="(bool) autocorrelation or not"
    )
    parser.add_argument(
        "-w", "--num_workers", type=int, default=None, help="num_workers"
    )
    args = parser.parse_args()

    validator = Validator(
        real_data_path=args.real_path,
        save_path=args.save_path,
        budget=args.budget,
        num_workers=args.num_workers,
        multi_var=args.multi_var,
        period=args.period,
    )
    validator.validate()

    print("Done.")
