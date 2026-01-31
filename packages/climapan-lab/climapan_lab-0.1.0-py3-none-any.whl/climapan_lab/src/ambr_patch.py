import time

import ambr
import polars as pl
from ambr.model import Model


def _robust_collect_results(self, start_time, max_steps):
    """
    Monkeypatched version of ambr.Model._collect_results to handle sparse data robustly.
    Fixes 'TypeError: object of type 'NoneType' has no len()' in Polars.
    """
    if self._model_data:
        # Column-oriented construction to avoid Polars concat ShapeErrors with sparse data
        all_keys = sorted(list(set().union(*(d.keys() for d in self._model_data))))
        data_dict = {k: [] for k in all_keys}

        for d in self._model_data:
            for k in all_keys:
                data_dict[k].append(d.get(k, None))

        series_list = []
        for k, v in data_dict.items():
            try:
                s = pl.Series(k, v, strict=False)
            except (TypeError, ValueError, Exception):
                # Fallback to Object type for columns with mixed None/Arrays
                # Explicitly handle cases where Polars fails to infer length of None
                try:
                    # Provide an explicit schema hint if possible, or just force Object
                    s = pl.Series(k, v, dtype=pl.Object, strict=False)
                except Exception:
                    # deeply robust fallback: cast everything to string if needed,
                    # or just create an object series from a list of wrapped objects
                    s = pl.Series(k, v, dtype=pl.Object)
            series_list.append(s)

        model_df = pl.DataFrame(series_list)
    else:
        model_df = pl.DataFrame({"t": []})

    return {
        "info": {"steps": self.t, "run_time": time.time() - start_time},
        "agents": self.population.data,
        "model": model_df,
    }


# Apply monkeypatch
Model._collect_results = _robust_collect_results
print("Applied robust monkeypatch to ambr.Model._collect_results")
