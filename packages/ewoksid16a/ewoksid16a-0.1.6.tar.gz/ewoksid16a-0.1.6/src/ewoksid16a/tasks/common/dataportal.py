#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul  6 20:10:52 2025

@author: blissadm
"""

from esrf_pathlib import ESRFPath
from ewokscore import Task
from pyicat_plus.client.main import IcatClient


class PublishProcessed(
    Task,
    input_names=["bliss_scan_file", "processed_folder", "icat_url"],
    optional_input_names=["beamline", "metadata", "dataset", "sample", "proposal"],
):
    """Publish processed data to data portal"""

    def run(self):
        raw_data = ESRFPath(self._fix_data_path(self.inputs["bliss_scan_file"]))
        data_folder = self._fix_data_path(self.inputs["processed_folder"])

        # Deduce from raw data path or get from optional inputs
        #        spath = raw_data.split("/")
        #        raw_data = os.path.dirname(raw_data)
        #        dataset = self.get_input_value(
        #            "dataset", spath[-2] if len(spath) >= 2 else None
        #        )
        #        sample = self.get_input_value(
        #            "sample", spath[-3] if len(spath) >= 3 else "sample"
        #        )
        #        beamline = self.get_input_value(
        #            "beamline", spath[-6] if len(spath) >= 6 else "id16a"
        #        )
        #        proposal = self.get_input_value(
        #            "proposal", spath[-7] if len(spath) >= 7 else None
        #        )

        metadata = self.get_input_value("metadata", {})

        if "Sample_name" not in metadata:
            metadata["Sample_name"] = raw_data.collection

        #        print(
        #            self.inputs["bliss_scan_file"],
        #            raw_data,
        #            data_folder,
        #            dataset,
        #            sample,
        #            beamline,
        #            proposal,
        #        )

        client = IcatClient(metadata_urls=self.inputs["icat_url"])
        client.store_processed_data(
            beamline=raw_data.beamline,
            proposal=raw_data.proposal,
            dataset=f"{raw_data.collection}_{raw_data.dataset}",
            path=data_folder,
            metadata=metadata,
            raw=raw_data.raw_dataset_path,
        )

    def _fix_data_path(self, path):
        if path.startswith("/mnt/multipath-shares/data"):
            path = path.replace("/mnt/multipath-shares/data", "/data")

        return path
