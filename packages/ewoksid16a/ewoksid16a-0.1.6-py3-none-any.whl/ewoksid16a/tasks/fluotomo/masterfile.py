#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov  1 17:01:47 2025

@author: blissadm
"""

import glob
import os

import h5py
from ewokscore import Task


class FluotomoMaster(
    Task,
    input_names=[
        "processed_dataset_folder",
    ],
    optional_input_names=["output_folder", "output_filename"],
    output_names=["output_master_file"],
):
    """Create a fluotomo master folder from all fluofit folders"""

    def run(self):
        inpath = self.inputs["processed_dataset_folder"]

        while inpath[-1] == "/":
            inpath = inpath[:-1]

        opath = self.inputs.get("output_folder")
        ofn = self.inputs.get("output_filename")

        if opath is None:
            opath = os.path.join(inpath, "fluotomo")

        datasetname = inpath.split("/")[-1]

        if ofn is None:
            ofn = datasetname + ".h5"

        os.makedirs(opath, exist_ok=True)
        os.chmod(opath, 0o770)  # nosec B103: group write required for shared pipeline

        masterfile = os.path.join(opath, ofn)
        self.outputs["output_master_file"] = masterfile

        with h5py.File(masterfile, "w") as ofd:
            for f in glob.glob(os.path.join(inpath, f"fluofit_*/{datasetname}.h5")):
                ss = f.split("/")[-2]
                if "scan" not in ss:
                    continue

                scanno = int(ss[-4:])
                # print(scanno)

                ofd[f"{scanno}.1"] = h5py.ExternalLink(f, f"/{scanno}.1")
