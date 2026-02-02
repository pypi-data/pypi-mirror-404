import os
import time
from threading import Lock

import matplotlib.pyplot as plt
import numpy as np
from ewokscore import Task
from PyMca5.PyMcaIO import ConfigDict
from PyMca5.PyMcaPhysics.xrf.ClassMcaTheory import ClassMcaTheory
from silx.io import h5py_utils

_mcaLock = Lock()


class AdvancedFitSumSingleDetector(
    Task,
    input_names=[
        "bliss_scan_uri",
        "detector_name",
        "config",
        "output_root_uri",
    ],
    optional_input_names=[
        "figure_filename",
        "batchconfig_suffix",
        "instrument_data_template",
        "batch_force",
        "waitForConfigFile",
        "retryPeriod",
        "retryN",
    ],
    output_names=[
        "bliss_scan_uri",
        "detector_name",
        "output_root_uri",
        "batch_config_filename",
    ],
):
    def run(self):
        input_uri = self.inputs.bliss_scan_uri
        output_uri = self.inputs.output_root_uri
        detector_name = self.inputs.detector_name
        config_file = self.inputs.config

        dettmpl = self.get_input_value("instrument_data_template", "instrument/{}/data")
        batch_suffix = self.get_input_value("batchconfig_suffix", None)
        batch_force = self.get_input_value(
            "batch_force",
            {
                "fit.stripflag": 0,
                "fit.fitweight": 0,
                "fit.linearfitflag": 1,
            },
        )
        waitForConfigFile = self.get_input_value("waitForConfigFile", True)
        retryPeriod = self.get_input_value("retryPeriod", 3)
        retryN = self.get_input_value("retryN", 1200)

        figure_filename = self.get_input_value("figure_filename", None)

        uris = input_uri.split("::")
        filename = uris[0]
        datpath = uris[1] + "/" + dettmpl.format(detector_name)

        if waitForConfigFile:
            for i in range(retryN):
                if os.path.isfile(config_file):
                    break
                time.sleep(retryPeriod)
            else:
                raise RuntimeError(f"Config file {config_file} not found!")

        with h5py_utils.open_item(filename, datpath) as ds:  # type: ignore[reportGeneralTypeIssues]
            data = np.array(ds)

        batch_savefile = None

        if batch_suffix is not None:
            batch_savefile = config_file[:-4] + batch_suffix

            if not os.path.isfile(batch_savefile):
                cfg = ConfigDict.ConfigDict(filelist=config_file)

                for k in batch_force:
                    _c = cfg
                    kk = k.split(".")
                    for _k in kk[:-1]:
                        _c = _c[_k]

                    _c[kk[-1]] = batch_force[k]

                cfg.write(batch_savefile)

        data = np.sum(data, keepdims=True, axis=0) / data.shape[0]

        with _mcaLock:
            mcafit = ClassMcaTheory(config_file)

        mcafit.setData(x=np.arange(data.shape[1]), y=data)
        mcafit.estimate()
        p, fit = mcafit.startfit(digest=1)

        egy = fit["energy"]
        bkg = fit["continuum"]
        grps = fit["groups"]
        yfit = fit["yfit"]
        ydata = fit["ydata"]

        ouris = output_uri.split("::")
        out_filename = ouris[0]
        out_path = ouris[1]

        with h5py_utils.open_item(out_filename, "/", mode="a") as fd:  # type: ignore[reportGeneralTypeIssues]
            _res = fd
            for g in out_path.split("/"):
                _g = g.strip()
                if len(_g) == 0:
                    continue

                _res = _res.require_group(_g)
                _res.attrs["NX_class"] = "NXcollection"

            _res.attrs["NX_class"] = "NXdata"
            _res.attrs["signal"] = "fit"
            _res.attrs["auxiliary_signals"] = [
                "background",
                "spectrum",
            ] + grps
            _res.attrs["axes"] = ["energy"]

            egyds = _res.create_dataset("energy", data=egy)
            egyds.attrs["units"] = "keV"

            _res.create_dataset("fit", data=yfit)
            _res.create_dataset("spectrum", data=ydata)
            _res.create_dataset("background", data=bkg)

            for g in grps:
                _res.create_dataset(g, data=fit[f"y{g}"])

        if figure_filename is not None:
            figpath = os.path.dirname(figure_filename)
            os.makedirs(figpath, exist_ok=True)
            os.chmod(figpath, 0o770)  # nosec B103: group write required!

            fig, ax = plt.subplots(figsize=(8, 5), layout="constrained")
            colors = plt.get_cmap("nipy_spectral")(np.linspace(0.1, 0.9, len(grps)))

            ax.plot(egy, ydata, "-", color="0.7", label="Data", linewidth=4)
            # ax.plot(egy, yfit, 'r-', label="Fit", linewidth=2)

            for c, g in zip(colors, grps):
                ax.plot(egy, fit[f"y{g}"] + bkg, "--", label=g, linewidth=1.5, color=c)

            ax.plot(egy, bkg, "b", label="Background", linewidth=2)

            fig.legend(loc="outside right upper")

            ax.set_yscale("log")
            ax.set_xlabel("Energy (keV)")

            fig.savefig(figure_filename)

        self.outputs.output_root_uri = output_uri
        self.outputs.detector_name = detector_name
        self.outputs.bliss_scan_uri = input_uri
        self.outputs.batch_config_filename = batch_savefile
