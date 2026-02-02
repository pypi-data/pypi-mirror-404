import os

import h5py
from ewokscore import Task


class AddEntryToMasterfile(
    Task,
    input_names=["masterfile_uri", "nxtomo_uri"],
    optional_input_names=[],
    output_names=["masterfile_uri"],
):
    """
    This task add or replace an entry in the masterfile
    """

    def run(self):
        masterfile_uri = self.inputs["masterfile_uri"].split("::/")

        masterfile_filepath = masterfile_uri[0]
        masterfile_entry = masterfile_uri[1]

        nxtomo_uri = self.inputs["nxtomo_uri"].split("::")

        nxtomo_filepath = nxtomo_uri[0]
        nxtomo_entry = nxtomo_uri[1]

        relpath = os.path.relpath(nxtomo_filepath, os.path.dirname(masterfile_filepath))

        with h5py.File(masterfile_filepath, "a") as fd:
            if masterfile_entry in fd:
                del fd[masterfile_entry]

            fd[masterfile_entry] = h5py.ExternalLink(relpath, nxtomo_entry)

        self.outputs["masterfile_uri"] = self.inputs["masterfile_uri"]
