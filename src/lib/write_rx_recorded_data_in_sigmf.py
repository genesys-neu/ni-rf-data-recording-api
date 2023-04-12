#
# Copyright 2022 National Instruments Corporation
#
# SPDX-License-Identifier: MIT
#
"""
Save data and meta-data interface - SigMF format
"""
# Description:
#   Write data and meta-data to files in SigMF format
#
# To write Data to sigmf file
# To save to specific path
import os
import sigmf
import datetime as dt
from sigmf import SigMFFile
from sigmf.utils import get_data_type_str
import numpy as np
from lib import data_format_conversion_lib

# To use data time
from datetime import datetime


def write_rx_recorded_data_in_sigmf(rx_data, rx_args, txs_args, general_config, idx):
    # Check the receive target path is valid, else create folder
    if not os.path.isdir(rx_args.rx_recorded_data_path):
        print("Create new folder for recorded data: " + str(rx_args.rx_recorded_data_path))
        os.makedirs(rx_args.rx_recorded_data_path)

    # Write recorded data to file
    # Get time stamp
    print(general_config["use_tx_timestamp"])
    if data_format_conversion_lib.str2bool(general_config["use_tx_timestamp"]):
        prefix_length = len("tx_waveform_")
        time_stamp_milli_sec = txs_args[0].waveform_file_name[prefix_length:]
    else:
        time_stamp_micro_sec = datetime.now().strftime("%Y_%m_%d-%H_%M_%S_%f")
        time_stamp_milli_sec = time_stamp_micro_sec[:-3]

    rx_data_file_name = rx_args.captured_data_file_name + str(idx) + "-" + time_stamp_milli_sec
    dataset_filename = rx_data_file_name + ".sigmf-data"
    dataset_file_path = os.path.join(rx_args.rx_recorded_data_path, dataset_filename)
    print(dataset_file_path)
    rx_data.tofile(dataset_file_path)

    # Create sigmf metadata
    # ----------------------
    # Add global parameters to SigMF metadata
    # ----------------------
    meta = SigMFFile(
        data_file=dataset_file_path,  # extension is optional
        global_info={
            SigMFFile.DATATYPE_KEY: "cf32_le",  # get_data_type_str(rx_data) - 'cf64_le' is not supported yet
            SigMFFile.SAMPLE_RATE_KEY: rx_args.coerced_rx_rate,  # args.rate,
            SigMFFile.NUM_CHANNELS_KEY: len(rx_args.channels),
            SigMFFile.AUTHOR_KEY: general_config["author"],
            SigMFFile.DESCRIPTION_KEY: general_config["description"],
            SigMFFile.RECORDER_KEY: "Using NI RF Data Recording API: https://github.com/genesys-neu/ni-rf-data-recording-api",
            SigMFFile.LICENSE_KEY: "MIT License",
            SigMFFile.HW_KEY: rx_args.hw_type,
            # Disable DATASET key to mitigate the warning when read SIGMF data although it is given in the spec.
            # It seems SIGMF still has bug here
            # SigMFFile.DATASET_KEY: dataset_filename,
            SigMFFile.VERSION_KEY: sigmf.__version__,
        },
    )

    # ----------------------
    # Add capture parameters to SigMF metadata
    # ----------------------
    meta.add_capture(
        0,  # Sample Start
        metadata={
            SigMFFile.FREQUENCY_KEY: rx_args.coerced_rx_freq,
            SigMFFile.DATETIME_KEY: dt.datetime.utcnow().isoformat() + "Z",
        },
    )

    # Get tx waveform config
    txs_info = [{} for sub in range(len(txs_args))]
    channel_info = [{} for sub in range(len(txs_args))]
    label = ""

    for idx, tx_args in enumerate(txs_args):
        signal_detail = tx_args.waveform_config
        standard = signal_detail["standard"]
        signal_info = {}
        for key, value in signal_detail.items():
            if key != "standard" and key != "generator":
                signal_info[key] = value
        # signal_detail.pop("standard")
        if idx == 0:
            label = standard
        else:
            label = label + "_" + standard

        signal_emitter = {
            "manufacturer": "NI",
            "seid": tx_args.seid,  # Unique ID of the emitter
            "hw": tx_args.hw_type,
            "hw_subtype": tx_args.hw_subtype,
            "frequency": tx_args.freq,
            "sample_rate": tx_args.rate,
            "bandwidth": tx_args.max_RF_bandwidth,
            "gain_tx": np.float32(tx_args.gain).item(),
            "clock_reference": tx_args.clock_reference,
        }

        txs_info[idx] = {
            "transmitter_id": str(idx),
            "signal:detail": {
                "standard": standard,
                "generator": signal_detail["generator"],
                standard: signal_info,
            },
            "signal:emitter": signal_emitter,
        }

        # get channel info
        channel_info[idx] = {
            "transmitter_id": str(idx),
            "attenuation_db": float(rx_args.channel_attenuation_db),
        }

    # get rx info
    rx_info = {
        "manufacturer": "NI",
        "seid": rx_args.seid,
        "hw_subtype": rx_args.hw_subtype,
        "clock_reference": rx_args.clock_reference,
        "bandwidth": rx_args.coerced_rx_bandwidth,
        "gain": rx_args.coerced_rx_gain,
    }

    # ----------------------
    # Add annotation parameters to SigMF metadata
    # ----------------------
    meta.add_annotation(
        0,  # Sample Start
        rx_args.num_rx_samps,  # Sample count
        metadata={
            SigMFFile.FLO_KEY: rx_args.coerced_rx_freq
            - rx_args.coerced_rx_rate / 2,  # args.freq - args.rate / 2,
            SigMFFile.FHI_KEY: rx_args.coerced_rx_freq
            + rx_args.coerced_rx_rate / 2,  # args.freq + args.rate / 2,
            SigMFFile.LABEL_KEY: label,
            SigMFFile.COMMENT_KEY: general_config["comment"],
            "num_transmitters": len(txs_args),
            "system_components:transmitter": txs_info,
            "system_components:channel": channel_info,
            "system_components:receiver": rx_info,
        },
    )

    # Check for mistakes
    assert meta.validate()

    ## Write Meta Data to file
    dataset_meta_filename = rx_data_file_name + ".sigmf-meta"
    dataset_meta_file_path = os.path.join(rx_args.rx_recorded_data_path, dataset_meta_filename)
    meta.tofile(dataset_meta_file_path)  # extension is optional

    print(dataset_meta_file_path)


# Get tx waveform config from file name
# example:
#         waveform name: ["NR_FR1_DL_FDD_SISO_BW-20MHz_CC-1_SCS-30kHz_Mod-64QAM_OFDM_TM3.1.tdms"]},
#         ['NR', 'FR1', 'DL', 'FDD', 'SISO', 'BW-20MHz', 'CC-1', 'SCS-30kHz', 'Mod-64QAM', 'OFDM']
# Note: Function not used anymore
def get_tx_waveform_config_info(waveform_file_name):
    num_waveform_config_info = waveform_file_name.count("_")
    temp = waveform_file_name
    tx_waveform_config = []
    for i in range(num_waveform_config_info):
        tx_waveform_config.append(temp[0 : temp.find("_")])
        temp = temp[temp.find("_") + 1 :]

    return tx_waveform_config
