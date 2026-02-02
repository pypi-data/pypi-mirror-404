from typing import Sequence

import h5py  # noqa: F401
import hdf5plugin  # noqa: F401
import numpy
from ewokscore import Task
from ewoksfluo.io.hdf5 import split_h5uri
from ewoksfluo.tasks import nexus_utils
from ewoksfluo.tasks.hdf5_utils import create_hdf5_link
from ewoksfluo.tasks.hdf5_utils import link_bliss_scan

# from ewoksfluo.io.hdf5 import ReadHdf5File
from ewoksfluo.tasks.math import eval_hdf5_expression
from ewoksfluo.tasks.math import format_expression_template
from silx.io import h5py_utils

DEFAULTS = {
    "xrf_spectra_uri_template": "instrument/{}/data",
    "detector_normalization_template": "1./<instrument/{}/live_time>",
    "output_detector_name": "mcasum",
}


class SumXrfSpectra(
    Task,
    input_names=[
        "bliss_scan_uri",
        "detector_names",
        "output_root_uri",
    ],
    optional_input_names=[
        "xrf_spectra_uri_template",
        "detector_normalization_template",
        "output_detector_name",
    ],
    output_names=[
        "bliss_scan_uri",
        "detector_name",
        "xrf_spectra_uri_template",
        "output_root_uri",
    ],
):
    """Add single-scan XRF spectra from multiple detectors"""

    def run(self):
        start_time = nexus_utils.now()
        params = {**DEFAULTS, **self.get_input_values()}

        bliss_scan_uri: str = params["bliss_scan_uri"]
        detector_names: Sequence[str] = params["detector_names"]
        xrf_spectra_uri_template: str = params["xrf_spectra_uri_template"]
        detector_normalization_template: str = params["detector_normalization_template"]
        output_root_uri: str = params["output_root_uri"]

        if len(detector_names) < 1:
            raise ValueError("Expected at least 1 detector to sum")

        _, scan_h5path = split_h5uri(bliss_scan_uri)

        sumdetector_name = params["output_detector_name"]

        print("BeforeWith")
        with nexus_utils.save_in_ewoks_process(
            output_root_uri,
            start_time,
            process_config={
                "detector_normalization_template": detector_normalization_template
            },
            default_levels=(scan_h5path, "sumspectra"),
        ) as (process_group, already_existed):
            outentry = process_group.parent
            print(outentry)
            if not already_existed:
                print("NOT EXIST, DOING")
                sum_spectra = _sum_spectra(
                    bliss_scan_uri,
                    xrf_spectra_uri_template,
                    detector_names,
                    detector_normalization_template,
                )
                print("AFTERSUM")

                link_bliss_scan(outentry, bliss_scan_uri, retry_timeout=0)

                print("AFTERLINK")

                nxdata = nexus_utils.create_nxdata(
                    process_group, "mcasum", signal="data"
                )
                nxdata.attrs["interpretation"] = "spectrum"

                #                Optimum compression but less portable....
                #                dset = nxdata.create_dataset("data", data=sum_spectra, chunks=(1, sum_spectra.shape[1]), compression=hdf5plugin.Bitshuffle(cname="lz4"))
                dset = nxdata.create_dataset(
                    "data",
                    data=sum_spectra,
                    chunks=(1, sum_spectra.shape[1]),
                    compression="gzip",
                    shuffle=True,
                )

                nxdetector = outentry["instrument"].create_group(sumdetector_name)
                nxdetector.attrs["NX_class"] = "NXdetector"
                create_hdf5_link(nxdetector, "data", dset)
                create_hdf5_link(outentry["measurement"], sumdetector_name, dset)

            output_root_uri = f"{outentry.file.filename}::{outentry.name}"

        self.outputs.bliss_scan_uri = output_root_uri
        self.outputs.detector_name = sumdetector_name
        self.outputs.xrf_spectra_uri_template = DEFAULTS["xrf_spectra_uri_template"]
        self.outputs.output_root_uri = output_root_uri


def _sum_spectra(
    bliss_scan_uri: str,
    xrf_spectra_uri_template: str,
    detector_names: str,
    detector_normalization_template: str,
) -> numpy.ndarray:
    """Add spectra from multiple detectors after normalizing the spectra to a common live time."""
    input_file, scan_h5path = split_h5uri(bliss_scan_uri)
    #    with ReadHdf5File(input_file) as h5file:
    with h5py_utils.open_item(input_file, "/") as h5file:
        sum_spectra = None
        scan_group = h5file[scan_h5path]

        for detector_name in detector_names:
            print(detector_name)
            xrf_spectra_dataset = scan_group[
                xrf_spectra_uri_template.format(detector_name)
            ]
            print(xrf_spectra_dataset)
            # assert isinstance(xrf_spectra_dataset, h5py.Dataset)
            xrf_spectra_data = xrf_spectra_dataset[()]

            if (
                detector_normalization_template is not None
            ):  # Allow to get an unnormalized sum
                weight_expression = format_expression_template(
                    detector_normalization_template, detector_name
                )
                weight = eval_hdf5_expression(bliss_scan_uri, weight_expression)
                weight = weight.reshape((len(weight), 1))

                xrf_spectra_data *= weight

            if sum_spectra is None:
                sum_spectra = xrf_spectra_data
            else:
                sum_spectra += xrf_spectra_data

    return sum_spectra
