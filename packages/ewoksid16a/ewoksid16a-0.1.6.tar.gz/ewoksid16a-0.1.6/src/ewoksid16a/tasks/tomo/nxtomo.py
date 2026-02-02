import os
from datetime import datetime as dt

import numpy as np
import pint
from esrf_pathlib import ESRFPath
from ewokscore import Task
from h5py import VirtualSource
from nxtomo import NXtomo
from nxtomo.nxobject.nxdetector import ImageKey
from silx.io import h5py_utils
from silx.io.url import DataUrl

ureg = pint.UnitRegistry()


def _tostr(val):
    if isinstance(val, str):
        return val
    elif isinstance(val, bytes):
        return val.decode()
    else:
        return str(val)


class Tomo2Nx(
    Task,
    input_names=[
        "bliss_scan_uri",
    ],
    optional_input_names=["output_entry", "include_positioners"],
    output_names=["bliss_scan_uri", "output_root_uri"],
):
    """
    This task takes a fulltomo sequence and creates the associated NXtomo file.
    """

    def run(self):
        bliss_uri = self.inputs["bliss_scan_uri"]
        uri = bliss_uri.split("::/")

        bliss_filename = uri[0]
        scan_id = uri[1]

        scan_no = int(scan_id.split(".")[0])

        esrf_path = ESRFPath(bliss_filename)

        output_file = os.path.join(
            esrf_path.processed_dataset_path,
            "projections",
            f"{esrf_path.collection}_{esrf_path.dataset}_{scan_no:04d}.nx",
        )

        output_entry = self.get_input_value("output_entry", "entry")

        output_path = os.path.abspath(os.path.dirname(output_file))

        if not os.path.isdir(output_path):
            os.makedirs(output_path, exist_ok=True)
            os.chmod(
                output_path, 0o770
            )  # nosec B103: group write required for shared pipeline

        bliss_positioners_mapping = {
            "sample_u": "sample_u",
            "sample_v": "sample_v",
            "z_translation": "translation_x",
            "x_translation": "translation_y",
            "y_translation": "translation_z",
            "rotation_angle": "rotation",
        }
        motors_mapping = {}

        types_mapping = {
            "tomo:dark": ImageKey.DARK_FIELD,
            "tomo:flat": ImageKey.FLAT_FIELD,
            "tomo:step": ImageKey.PROJECTION,
            "tomo:return_ref": ImageKey.ALIGNMENT,
        }

        nxtomo = NXtomo()
        nxtomo.start_time = dt.now()
        nxtomo.bliss_original_files = (bliss_uri,)
        sy_pos = None
        dety = None

        positioners_start = {}

        # open the tomo seauence, read the configuration and scan sequence
        with h5py_utils.open_item(bliss_filename, scan_id) as tomo_sequence:
            nxtomo.energy = pint.Quantity(
                tomo_sequence["technique/scan/energy"][()], "keV"
            )
            nxtomo.instrument.detector.tomo_n = tomo_sequence["technique/scan/tomo_n"][
                ()
            ]

            sdist = tomo_sequence["technique/scan/sample_detector_distance"]
            nxtomo.instrument.detector.distance = ureg.Quantity(
                sdist[()], sdist.attrs.get("units", "mm")
            )

            ops_ds = tomo_sequence["technique/optic/optics_pixel_size"]
            ops = ureg.Quantity(ops_ds[()], ops_ds.attrs.get("units", "um"))
            nxtomo.instrument.detector.x_pixel_size = ops
            nxtomo.instrument.detector.y_pixel_size = ops

            sps_ds = tomo_sequence["technique/optic/sample_pixel_size"]
            sps = ureg.Quantity(sps_ds[()], ops_ds.attrs.get("units", "um"))
            nxtomo.sample.x_pixel_size = sps
            nxtomo.sample.y_pixel_size = sps

            ssd_ds = tomo_sequence["technique/scan/source_sample_distance"]
            ssd = ureg.Quantity(-ssd_ds[()], ssd_ds.attrs.get("units", "mm"))
            nxtomo.instrument.source.distance = ssd

            effd_ds = tomo_sequence["technique/scan/effective_propagation_distance"]
            effd = ureg.Quantity(effd_ds[()], effd_ds.attrs.get("units", "mm"))
            nxtomo.sample.propagation_distance = effd

            scan_numbers = tomo_sequence["subscans"]["scan_numbers"][:]
            detector = tomo_sequence["technique/tomoconfig/detector"][0]

            for k in tomo_sequence["instrument/positioners"]:
                ds = tomo_sequence["instrument/positioners"][k]
                positioners_start[k] = ureg.Quantity(
                    ds[()], ds.attrs.get("units", None)
                )

            for k, m in bliss_positioners_mapping.items():
                if m in tomo_sequence["technique/tomoconfig"]:
                    motors_mapping[k] = []

                    tot = None

                    for v in tomo_sequence["technique/tomoconfig"][m]:
                        pos_ds = tomo_sequence["instrument/positioners"][v]
                        units = pos_ds.attrs.get("units", None)
                        motors_mapping[k] += [(_tostr(v), units)]

                        if tot is None:
                            tot = ureg.Quantity(pos_ds[()], units)
                        else:
                            tot += ureg.Quantity(pos_ds[()], units)

                    if m == "translation_y":
                        sy_pos = tot

            detector_y_ds = tomo_sequence["technique/tomoconfig/detector_center_y"]
            dety = ureg.Quantity(
                detector_y_ds[()], detector_y_ds.attrs.get("units", "mm")
            )

            types = []
            for k in tomo_sequence["technique"]["subscans"]:
                typ = tomo_sequence["technique"]["subscans"][k]["type"][()]
                if isinstance(typ, bytes):
                    typ = typ.decode()
                types += [
                    typ,
                ]

        detector_data_url = []
        image_key_control = []
        positioners = {k: [] for k in motors_mapping}
        srcur = []
        count_time = []

        # Go so subscans and get infos

        shape = None

        for i, n in enumerate(scan_numbers):
            if types[i] not in types_mapping:  # Maybe a custom scan in the sequence
                continue

            with h5py_utils.open_item(bliss_filename, f"/{n}.1") as scan:
                det_ds = scan["measurement"][detector]
                shape = det_ds.shape
                n_images = det_ds.shape[0]

                pos = {k: np.zeros((n_images,), dtype=np.float32) for k in positioners}

                for k, v in motors_mapping.items():
                    for m in v:
                        posval = ureg.Quantity(
                            scan["instrument/positioners"][m[0]][()], m[1]
                        )
                        pos[k] += posval

                    positioners[k] += [
                        pos[k],
                    ]

                srcur += [scan["measurement/current"][()]]
                count_time_ds = scan["scan_parameters/count_time"]
                count_time += [
                    ureg.Quantity(
                        np.array(
                            [
                                count_time_ds[()],
                            ]
                            * n_images
                        ),
                        count_time_ds.attrs.get("units", "s"),
                    ),
                ]

                image_key_control += [
                    types_mapping[types[i]],
                ] * n_images
                if (
                    det_ds.is_virtual
                ):  # Resolve virtual datasets to avoid any pointers to bliss scan file if possible
                    for vs in det_ds.virtual_sources():
                        src_file = vs.file_name
                        src_path = vs.dset_name

                        if not os.path.isabs(src_file):
                            src_file = os.path.join(
                                os.path.dirname(bliss_filename), src_file
                            )

                        # src_file = os.path.relpath(src_file, output_path)

                        # print(src_file)

                        detector_data_url += [
                            VirtualSource(src_file, src_path, vs.src_space.shape),
                        ]
                else:
                    detector_data_url += [
                        DataUrl(
                            file_path=bliss_filename,
                            data_path=f"/{n}.1/measurement/{detector}",
                            scheme="silx",
                        ),
                    ]

        if sy_pos is not None and dety is not None:
            rotaxis_pos = ((sy_pos - dety) / sps).to_reduced_units()
            nxtomo.instrument.detector.x_rotation_axis_pixel_position = (
                shape[1] // 2 - rotaxis_pos.magnitude
            )

        # Sample positioners
        extra_positioners = []

        for k, v in positioners.items():
            try:
                setattr(nxtomo.sample, k, np.concatenate(v))
            except Exception as e:
                print(e)
                extra_positioners += [
                    k,
                ]

        nxtomo.sample.name = esrf_path.collection
        nxtomo.title = esrf_path.dataset

        nxtomo.control.data = np.concatenate(srcur)

        nxtomo.instrument.name = esrf_path.beamline
        nxtomo.instrument.detector.data = detector_data_url
        nxtomo.instrument.detector.count_time = np.concatenate(count_time)
        nxtomo.instrument.detector.image_key_control = image_key_control

        nxtomo.end_time = dt.now()
        nxtomo.save(output_file, output_entry, overwrite=True)

        if self.get_input_value("include_positioners", True):
            with h5py_utils.open_item(output_file, output_entry, mode="a") as fd:

                grp = fd.require_group("instrument/positioners")
                grp.attrs["NX_class"] = "NXcollection"

                for k, v in positioners_start.items():
                    if k in grp:
                        del grp[k]

                    grp[k] = np.float32(v.magnitude)
                    if v.units is not None:
                        grp[k].attrs["units"] = f"{v.units:~P}"

        self.outputs["bliss_scan_uri"] = self.inputs["bliss_scan_uri"]
        self.outputs["output_root_uri"] = output_file + "::/entry"
