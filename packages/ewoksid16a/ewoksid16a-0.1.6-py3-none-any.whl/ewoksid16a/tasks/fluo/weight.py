from typing import Sequence

import h5py
import hdf5plugin  # noqa: F401
import numpy as np
from ewokscore import Task
from ewoksfluo.tasks import xrf_results
from silx.io import h5py_utils

# from ewokscore import Task


# from ewoksfluo.io.hdf5 import ReadHdf5File


# from ewoksfluo.io.hdf5 import ReadHdf5File
# from ewoksfluo.tasks import xrf_results


class WeightedSumResults(
    Task,
    input_names=[
        "xrf_norm_uris",
        "xrf_fit_uris",
        "bliss_scan_uri",
        "detector_names",
        "output_root_uri",
    ],
    optional_input_names=["detector_normalization_template"],
    output_names=["xrf_results_uri", "bliss_scan_uri", "output_root_uri"],
):
    """Add single-scan XRF results of multiple detectors"""

    def _read_xrf_results(self, uri):
        res = dict()

        fit_filename, fit_h5path = uri.split("::")

        fit_h5path += "/results"

        #        with ReadHdf5File(fit_filename) as h5file:

        with h5py_utils.open_item(fit_filename, "/") as h5file:
            try:
                xrf_results_group = h5file[fit_h5path]
            except KeyError:
                raise KeyError(
                    f"HDF5 path not found: '{fit_h5path}' in file '{fit_filename}'"
                )
            if not isinstance(xrf_results_group, h5py.Group):
                raise TypeError(
                    f"Expected HDF5 Group at '{fit_h5path}', but got {type(xrf_results_group)}"
                )

            if "massfractions" not in xrf_results_group:
                raise KeyError(f"'massfractions' group missing under '{fit_h5path}'")
            param_group = xrf_results_group["massfractions"]
            if not isinstance(param_group, h5py.Group):
                raise TypeError(
                    f"Expected HDF5 Group for 'massfractions', but got {type(param_group)}"
                )

            for dset_name, dset in param_group.items():
                if not xrf_results.is_peak_area(dset):
                    continue

                res[dset_name] = np.array(param_group[dset_name][()])

        return res

    def _dict_op(self, fun, a, b):
        ka = set(a.keys())
        kb = set(b.keys())

        s = dict()

        for k in set.intersection(ka, kb):
            s[k] = fun(a[k], b[k])

        return s

    def dict_op(self, fun, *op):
        if len(op) <= 1:
            return op

        res = self._dict_op(fun, op[0], op[1])

        for i in range(2, len(op)):
            res = self._dict_op(fun, res, op[i])

        return res

    def dict_plus(self, *op):
        return self.dict_op(lambda a, b: a + b, *op)

    def dict_mult(self, *op):
        return self.dict_op(lambda a, b: a * b, *op)

    def run(self) -> None:
        params = {**self.get_input_values()}

        xrf_norm_uris: Sequence[str] = params["xrf_norm_uris"]
        xrf_fit_uris: Sequence[str] = params["xrf_fit_uris"]
        bliss_scan_uri: str = params["bliss_scan_uri"]
        output_root_uri: str = params["output_root_uri"]

        if len(xrf_norm_uris) < 1:
            raise ValueError("Expected at least 1 detector to sum")

        if len(xrf_norm_uris) != len(xrf_fit_uris):
            raise ValueError(
                "Expected the same number of elements in _norm_ and _fit_ arrays."
            )

        summed_fit = None
        summed_prod = None

        config = {"xrf_norm_uris": xrf_norm_uris, "xrf_fit_uris": xrf_fit_uris}

        for norm_uri, fit_uri in zip(xrf_norm_uris, xrf_fit_uris):
            norm_data = self._read_xrf_results(norm_uri)
            fit_data = self._read_xrf_results(fit_uri)

            if summed_fit is None:
                summed_fit = fit_data
            else:
                summed_fit = self.dict_plus(summed_fit, fit_data)

            if summed_prod is None:
                summed_prod = self.dict_mult(norm_data, fit_data)
            else:
                summed_prod = self.dict_plus(
                    summed_prod, self.dict_mult(norm_data, fit_data)
                )

        weighted = self._dict_op(lambda a, b: a / b, summed_prod, summed_fit)

        xrf_results.save_xrf_results(
            output_root_uri,
            "weighted_ngmm2",
            config,
            None,
            None,
            weighted,
        )

        self.outputs.bliss_scan_uri = bliss_scan_uri
        self.outputs.output_root_uri = output_root_uri
        self.outputs.xrf_results_uri = output_root_uri + "/results"
