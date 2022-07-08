##! Write RX Data to a file in SigMF Format
#
# Copyright 2022 NI Dresden
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# To write Data to sigmf file
# To save to specific path
import os
import sigmf
import datetime as dt
from sigmf import SigMFFile
from sigmf.utils import get_data_type_str

# To use data time
from datetime import datetime


def write_rx_recorded_data_in_sigmf(rx_data, rx_args, txs_args, general_config):
    # Write recorded data to file
    # Get time stamp
    time_stamp_micro_sec = datetime.now().strftime("%Y_%m_%d-%H_%M_%S_%f")
    time_stamp_milli_sec = time_stamp_micro_sec[:-3]

    rx_data_file_name = "rx_data_record_" + time_stamp_milli_sec
    dataset_filename = rx_data_file_name + ".sigmf-data"
    dataset_file_path = os.path.join(rx_args.rx_recorded_data_path, dataset_filename)
    print(dataset_file_path)
    rx_data.tofile(dataset_file_path)

    # Create sigmf metadata
    meta = SigMFFile(
        data_file=dataset_file_path,  # extension is optional
        global_info={
            SigMFFile.DATATYPE_KEY: "cf32_le",  # get_data_type_str(rx_data) - 'cf64_le' is not supported yet
            SigMFFile.SAMPLE_RATE_KEY: rx_args.coerced_rx_rate,  # args.rate,
            SigMFFile.NUM_CHANNELS_KEY: len(rx_args.channels),
            SigMFFile.AUTHOR_KEY: general_config["author"],
            SigMFFile.DESCRIPTION_KEY: general_config["description"],
            SigMFFile.RECORDER_KEY: "NI RF Data Recording API",
            SigMFFile.LICENSE_KEY: "URL to the license document",
            SigMFFile.HW_KEY: rx_args.hw_type,
            SigMFFile.DATASET_KEY: dataset_filename,
            SigMFFile.VERSION_KEY: sigmf.__version__,
        },
    )

    # Create a capture key at time index 0
    meta.add_capture(
        0,  # Sample Start
        metadata={
            SigMFFile.FREQUENCY_KEY: rx_args.coerced_rx_freq,  # args.freq,
            SigMFFile.DATETIME_KEY: dt.datetime.utcnow().isoformat() + "Z",
            "capture_details": {
                "acquisition_bandwidth": rx_args.coerced_rx_bandwidth,
                "gain": rx_args.coerced_rx_gain,
                # "source_file": os.path.basename(__file__),  # RF IQ recording filename that was used to create the file
            },
        },
    )

    # Get tx waveform config
    txs_info = {}
    label = ""
    for idx, tx_args in enumerate(txs_args):
        tx_waveform_config = tx_args.waveform_config
        if idx == 0:
            label = tx_waveform_config["standard"]
        else:
            label = label + "_" + tx_waveform_config["standard"]
        signal_detail = {
            "standard": tx_waveform_config["standard"],
            "frequency_range": tx_waveform_config["frequency_range"],
            "link_direction": tx_waveform_config["link_direction"],
            "test_model": tx_waveform_config["test_model"],
            "bandwidth": str(tx_args.bandwidth),
            "subcarrier_spacing": tx_waveform_config["subcarrier_spacing"],
            "duplexing": tx_waveform_config["duplexing"],
            "multiplexing": tx_waveform_config["multiplexing"],
            "multiple_access": tx_waveform_config["multiple_access"],
            "modulation": tx_waveform_config["modulation"],
            "MCS": tx_waveform_config["MCS"],
            "code_rate": tx_waveform_config["code_rate"],
        }
        if "IEEE" in tx_waveform_config["standard"]:
            signal_detail["MAC_frame_type"] = tx_waveform_config["IEEE_MAC_frame_type"]

        signal_emitter = {
            "seid": tx_args.seid,  # Unique ID of the emitter
            "hw": tx_args.hw_type,
            "hw_subtype": tx_args.hw_subtype,
            "manufacturer": "NI",
            "frequency": str(tx_args.freq),
            "sample_rate": str(tx_args.rate),
            "bandwidth": str(tx_args.max_RF_bandwidth),
            "gain_tx": str(tx_args.gain),
            "clock_reference": tx_args.clock_reference,
        }
        # Filter out empty parameters (temporary, this step will be done after adding the parameter map)
        signal_detail_filtered = {}
        for i, value in signal_detail.items():
            if len(value):
                signal_detail_filtered[i] = value

        txs_info["Tx_" + str(idx)] = {
            "signal:detail": signal_detail_filtered,
            "signal:emitter": signal_emitter,
        }

    # get channel info
    channel_info = {
        "attenuation": int(rx_args.channel_attenuation),
    }
    # get rx info
    rx_info = {
        "seid": rx_args.seid,
        "hw_subtype": rx_args.hw_subtype,
        "manufacturer": "NI",
        "clock_reference": rx_args.clock_reference,
        "bandwidth": str(rx_args.max_RF_bandwidth),
    }
    # Add an annotation
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
            "num_tx_signals": len(txs_args),
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
    print("")


# Get tx waveform config from file name
# example:
#         waveform name: ["NR_FR1_DL_FDD_SISO_BW-20MHz_CC-1_SCS-30kHz_Mod-64QAM_OFDM_TM3.1.tdms"]},
#         ['NR', 'FR1', 'DL', 'FDD', 'SISO', 'BW-20MHz', 'CC-1', 'SCS-30kHz', 'Mod-64QAM', 'OFDM']
# to do: Enhance the list to be as a dictonary
def get_tx_waveform_config_info(waveform_file_name):
    num_waveform_config_info = waveform_file_name.count("_")
    temp = waveform_file_name
    tx_waveform_config = []
    for i in range(num_waveform_config_info):
        tx_waveform_config.append(temp[0 : temp.find("_")])
        temp = temp[temp.find("_") + 1 :]

    return tx_waveform_config
