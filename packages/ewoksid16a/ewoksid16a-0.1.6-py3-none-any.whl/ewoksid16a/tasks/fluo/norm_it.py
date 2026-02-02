import os
from configparser import ConfigParser

import numpy as np
from ewokscore import Task
from ewoksfluo.tasks import nexus_utils
from ewoksfluo.tasks.hdf5_utils import create_hdf5_link
from ewoksfluo.tasks.hdf5_utils import link_bliss_scan
from silx.io import h5py_utils


class NormalizeCurrent(
    Task,
    input_names=[
        "bliss_scan_uri",
        "output_root_uri",
        "current_counter",
        "reference_uri",
        "dwelltime_counter",
        "ref_current_counter",
        "diode_factor",
    ],
    optional_input_names=["gamma_coef", "min_ref", "max_ref", "exp_default"],
    output_names=["bliss_scan_uri", "output_root_uri"],
):
    def run(self):
        start_time = nexus_utils.now()
        bliss_scan_uri = self.inputs.bliss_scan_uri
        output_root_uri = self.inputs.output_root_uri
        scanuris = bliss_scan_uri.split("::")

        filename = scanuris[0]
        scanno = scanuris[1]

        counter_template = f"/{scanno}/instrument/%s/data"

        ref_scanuris = self.inputs.reference_uri.split("::")

        ref_filename = ref_scanuris[0]
        ref_scanno = ref_scanuris[1]

        ref_counter_template = f"/{ref_scanno}/instrument/%s/data"

        # Wait for scan to be finished first, up to one hour.
        with h5py_utils.open_item(
            filename,
            f"/{scanno}/end_time",
            retry_invalid=True,
            retry_timeout=3600,
            retry_period=5,
        ) as end_time:
            print(f"Scan finished at {end_time[()]}")

        with h5py_utils.open_item(
            ref_filename, ref_counter_template % self.inputs["ref_current_counter"]
        ) as ds:  # type: ignore[reportGeneralTypeIssues]
            # ref_epoch  = np.array(fd[ref_counter_template%self.inputs.get("ref_epoch_counter", "epoch")])
            ref_values = np.array(ds)

        with h5py_utils.open_item(filename, "/") as fd:  # type: ignore[reportGeneralTypeIssues]
            # epoch  = np.array(fd[ref_counter_template%self.inputs.get("data_epoch_counter", "epoch_trig")])
            values = np.array(fd[counter_template % self.inputs["current_counter"]])
            dwelltime = np.mean(fd[counter_template % self.inputs["dwelltime_counter"]])

        min_ref = self.get_input_value("min_ref", 1e8)
        max_ref = self.get_input_value("max_ref", 1e15)

        diode_factor = self.inputs.diode_factor * 1e12  # Convert ph/pA to ph/A

        ref_msk = np.logical_and(
            ref_values * diode_factor > min_ref, ref_values * diode_factor < max_ref
        )  # When shutter was open and not saturated

        #        ref_epoch = ref_epoch[ref_msk]
        ref_values = ref_values[ref_msk]

        gamma = np.mean(values) / (np.mean(ref_values) * dwelltime)
        gamma_coef = self.get_input_value("gamma_coef", 2.0)

        real_gamma_exp = np.log10(gamma / gamma_coef)
        gamma_exp = np.round(real_gamma_exp)

        gamma = gamma_coef * 10**gamma_exp

        with nexus_utils.save_in_ewoks_process(
            output_root_uri,
            start_time,
            process_config={"real_gamma_exp": real_gamma_exp, "gamma_exp": gamma_exp},
            default_levels=(scanno, "scaled_it"),
        ) as (process_group, already_existed):
            outentry = process_group.parent
            if not already_existed:
                link_bliss_scan(outentry, bliss_scan_uri, retry_timeout=0)

                nxdata = nexus_utils.create_nxdata(
                    process_group, "scaled_it", signal="data"
                )
                nxdata.attrs["interpretation"] = "spectrum"
                dset = nxdata.create_dataset("data", data=values / gamma * diode_factor)

                nxdetector = outentry["instrument"].create_group("scaled_it")
                nxdetector.attrs["NX_class"] = "NXdetector"
                create_hdf5_link(nxdetector, "data", dset)
                create_hdf5_link(outentry["measurement"], "scaled_it", dset)

            output_root_uri = f"{outentry.file.filename}::{outentry.name}"

        self.outputs.bliss_scan_uri = bliss_scan_uri
        self.outputs.output_root_uri = output_root_uri

        output_filepath = output_root_uri.split("::")[0]
        dirn = os.path.dirname(output_filepath)

        os.chmod(dirn, 0o770)  # nosec B103: group write required for shared pipeline
        os.chmod(
            output_filepath, 0o770
        )  # nosec B103: group write required for shared pipeline


class NormalizationFactorFromConfig(
    Task,
    input_names=["bliss_scan_uri", "xrf_results_uri", "config_file"],
    output_names=[
        "bliss_scan_uri",
        "xrf_results_uri",
        "counter_normalization_template",
    ],
):
    def get_from_cfg(self, cfg):
        cp = ConfigParser()
        cp.read(cfg)

        flux = cp.getfloat("concentrations", "flux")
        dwelltime = cp.getfloat("concentrations", "time")

        matrix = cp.get("attenuators", "Matrix")
        matdat = matrix.replace(" ", "").split(",")
        matrix_composition = matdat[1]
        matrix_density = float(matdat[2])
        matrix_thickness = float(matdat[3])
        print("INFO FROM CONFIG FILE")
        print("Config input flux: {0:g} (ph/s)".format(flux))
        print("Config dwell time: {0} (s)".format(dwelltime))
        print("Matrix composition: {0}".format(matrix_composition))
        print("Matrix density: {0} (g/cm**3)".format(matrix_density))
        print("Matrix thickness: {0} (cm)".format(matrix_thickness))
        areal_dens_ratio = matrix_density * matrix_thickness * 1e7  # ng/mm**2
        return flux, areal_dens_ratio, dwelltime

    def run(self):
        self.outputs.bliss_scan_uri = self.inputs.bliss_scan_uri
        self.outputs.xrf_results_uri = self.inputs.xrf_results_uri

        cfg_flux, areal_dens_ratio, cfg_dwelltime = self.get_from_cfg(
            self.inputs.config_file
        )

        factor = cfg_flux * cfg_dwelltime * areal_dens_ratio

        self.outputs.counter_normalization_template = (
            f"{factor:.04e}/<instrument/{{}}/data>"
        )
