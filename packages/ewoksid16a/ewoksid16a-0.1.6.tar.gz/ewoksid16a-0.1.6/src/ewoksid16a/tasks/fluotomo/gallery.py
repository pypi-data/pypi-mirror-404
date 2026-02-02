#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov  1 17:02:10 2025

@author: blissadm
"""

import os

import h5py
import imageio
import numpy as np
from ewokscore import Task


class AnimatedWebP(
    Task,
    input_names=["master_file", "detector_name"],
    output_names=["output_master_file"],
):
    """Create a fluotomo master folder from all fluofit folders"""

    def run(self):
        masterfile = self.inputs["master_file"]
        detname = self.inputs["detector_name"]
        self.outputs["output_master_file"]

        maps = {}
        shapes = {}
        somega = {}

        with h5py.File(masterfile, "r", locking=False) as fd:
            for e in fd:
                somega[e] = fd[e]["instrument/positioners/somega"][()]

                if "grid" not in fd[e]:
                    continue

                gridname = f"grid_{detname}_ng_mm2"

                if gridname not in fd[e]["grid"]:
                    continue

                group = fd[e]["grid"][gridname]["results/massfractions"]

                for g in group:
                    if len(group[g].shape) != 2:
                        continue

                    if g not in maps:
                        maps[g] = {}

                    if group[g].shape not in shapes:
                        shapes[group[g].shape] = 0

                    maps[g][e] = np.array(group[g])
                    shapes[group[g].shape] += 1

        mx = 0
        shp = None

        for sh in shapes:
            if shapes[sh] > mx:
                shp = sh
                mx = shapes[sh]

        processed_data_folder = os.path.dirname(masterfile)
        galleryfolder = os.path.join(processed_data_folder, "gallery")
        os.makedirs(galleryfolder, exist_ok=True)
        os.chmod(
            galleryfolder, 0o770
        )  # nosec B103: group write required for shared pipeline

        ssomega = {k: v for k, v in sorted(somega.items(), key=lambda item: item[1])}

        for elm, G in maps.items():
            filtered = []
            entries = []

            mn = None
            Mx = None

            for entry in ssomega:
                M = G[entry]

                if M.shape != shp:
                    continue

                filtered += [
                    M,
                ]
                entries += [
                    entry,
                ]

                mm = np.min(M)
                MM = np.max(M)

                if mn is None or mm < mn:
                    mn = mm

                if Mx is None or MM > Mx:
                    Mx = MM

            filtered = np.array(filtered)
            converted = np.array((filtered - mn) / (Mx - mn) * 255, dtype=np.uint8)

            imageio.v3.imwrite(
                os.path.join(galleryfolder, f"{elm}.webp"), converted, fps=5
            )
