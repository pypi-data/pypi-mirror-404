#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os

import numpy as np
from esrf_pathlib import ESRFPath
from ewokscore import Task
from silx.io import h5py_utils


class ExtractRanddisp(
    Task,
    input_names=[
        "bliss_scan_uri",
    ],
    optional_input_names=[
        "output_filename",
    ],
    output_names=["bliss_scan_uri", "output_filename"],
):
    """
    This task extract the random displacement to text.
    """

    def run(self):
        bliss_uri = self.inputs["bliss_scan_uri"]
        uri = bliss_uri.split("::/")

        bliss_filename = uri[0]
        scan_id = uri[1]

        scan_no = int(scan_id.split(".")[0])

        esrf_path = ESRFPath(bliss_filename)

        output_filename = os.path.join(
            esrf_path.processed_dataset_path,
            "projections",
            f"{esrf_path.collection}_{esrf_path.dataset}_{scan_no:04d}.txt",
        )

        output_filename = self.get_input_value("output_filename", output_filename)

        output_path = os.path.abspath(os.path.dirname(output_filename))

        if not os.path.isdir(output_path):
            os.makedirs(output_path, exist_ok=True)
            os.chmod(
                output_path, 0o770
            )  # nosec B103: group write required for shared pipeline

        types = []
        # open the tomo seauence, read the configuration and scan sequence

        with h5py_utils.open_item(bliss_filename, scan_id) as tomo_sequence:
            scan_numbers = tomo_sequence["subscans"]["scan_numbers"][:]

            for k in tomo_sequence["technique"]["subscans"]:
                typ = tomo_sequence["technique"]["subscans"][k]["type"][()]
                if isinstance(typ, bytes):
                    typ = typ.decode()
                types += [
                    typ,
                ]

        disp_y_px = []
        disp_z_px = []

        for i, n in enumerate(scan_numbers):
            if types[i] == "tomo:step":  # Only valid for projections

                with h5py_utils.open_item(bliss_filename, f"/{n}.1") as scan:
                    disp_y_px += [scan["technique/proj/rand_pos_y_px"][()]]
                    disp_z_px += [scan["technique/proj/rand_pos_z_px"][()]]

            elif types[i] == "tomo:return_ref":  # add 3 zeros for return ref

                disp_y_px += [
                    np.zeros((3,), dtype=np.float32),
                ]
                disp_z_px += [
                    np.zeros((3,), dtype=np.float32),
                ]

        disp_y_px = np.concatenate(disp_y_px)
        disp_z_px = np.concatenate(disp_z_px)

        np.savetxt(output_filename, np.array([disp_y_px, -disp_z_px]).T, "%.03f")

        self.outputs["bliss_scan_uri"] = bliss_uri
        self.outputs["output_filename"] = output_filename
