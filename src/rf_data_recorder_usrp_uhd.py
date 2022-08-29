#
# Copyright 2022 National Instruments Corporation
#
# SPDX-License-Identifier: MIT
#
"""
RF Data Recorder (Rx Only)
"""
# Description:
#   Use for Rx data acquistion and save RX data and meta-data to files in SigMF format
#   User needs to specify Tx signal config detial and Tx HW info manually (signal_detail, signal_emitter)
#
# Parameters:
#   Look to parse the command line arguments
#
#   Pre-requests: Install UHD with Python API enabled
#

import argparse
from pickle import FALSE, TRUE
from unicodedata import name
import numpy as np
import uhd

# To save to specific path
import os
from pathlib import Path

# To measure elapsed time
import time

# To use data time
from datetime import datetime

# To print colours
import sys
from termcolor import colored, cprint

# To write Data to sigmf file
import sigmf
import datetime as dt
from sigmf import SigMFFile
from sigmf.utils import get_data_type_str


def parse_args():
    """Parse the command line arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a", "--args", default="type=x300,addr=192.168.40.2,master_clock_rate=184.32e6", type=str
    )
    parser.add_argument(
        "-o",
        "--rx_recorded_data_path",
        default=(Path(__file__).parent / "/home/user/workarea/recorded-data").resolve(),
        type=str,
    )
    parser.add_argument("-f", "--freq", default=2e9, type=float, help="RF center frequency in Hz")
    parser.add_argument("-r", "--rate", default=30.72e6, type=float, help="rate of radio block")
    parser.add_argument(
        "-d", "--duration", default=10e-3, type=float, help="time duration of IQ data acquisition"
    )
    parser.add_argument(
        "-c", "--channels", default=0, nargs="+", type=int, help="radio channel to use"
    )
    parser.add_argument("-g", "--gain", default=20, type=float, help="gain for the RF chain")
    parser.add_argument("-ant", "--antenna", default="TX/RX", type=str, help="antenna selection")
    parser.add_argument(
        "-ref",
        "--reference",
        default="internal",
        type=str,
        help="reference source (internal, external, gpsdo)",
    )
    parser.add_argument("-nr", "--nrecords", type=int, default=2)

    return parser.parse_args()


def main():

    # Get process api arguments
    args = parse_args()

    # Define number of samples to fetch
    num_samps = int(np.ceil(args.duration * args.rate))

    if not isinstance(args.channels, list):
        args.channels = [args.channels]

    # Initialize usrp
    print("Initialize usrp ...")
    usrp = uhd.usrp.MultiUSRP(args.args)

    # get USRP daughterboard ID, UBX, CBX ...etc
    usrp_info = usrp.get_usrp_rx_info()
    print("RX USRP info with default config:")
    print(usrp_info)
    usrp_daughterboard_id = usrp_info["rx_id"]
    temp = usrp_daughterboard_id.split(" ")
    usrp_daughterboard_id_wo_ref = temp[0]
    usrp_bandwidth = usrp.get_rx_bandwidth()
    # get USRP type, i.e. X310
    usrp_mboard_id = usrp_info["mboard_id"]
    # get USRP serial number
    usrp_serial_number = usrp_info["mboard_serial"]

    print("USRP info:")
    print(
        "usrp_mboard_id:",
        usrp_mboard_id,
        ", usrp_serial_number:",
        usrp_serial_number,
        ", usrp_daughterboard_id:",
        usrp_daughterboard_id_wo_ref,
        ", usrp_RF_bandwidth:",
        usrp_bandwidth,
    )
    hw_type = "USRP " + usrp_mboard_id
    hw_subtype = usrp_daughterboard_id_wo_ref
    seid = usrp_serial_number
    max_RF_bandwidth = usrp_bandwidth

    # Set clock reference
    print("Setup the clock reference ...")
    usrp.set_clock_source(args.reference)

    # Set up the stream
    print("Setup the stream ...")
    cpu_format = "fc32"
    wire_format = "sc16"
    st_args = uhd.usrp.StreamArgs(cpu_format, wire_format)
    st_args.channels = args.channels  # If you're only using one channel, then this is simply [0]
    rx_streamer = usrp.get_rx_stream(st_args)

    # Set TX/RX port as receive port
    for index in args.channels:
        usrp.set_rx_antenna(args.antenna, index)

    # run data recording loop over specified number of iterations
    print("Start fetching RX data from USRP...")
    for i in range(args.nrecords):
        # fetch data from usrp device
        start_time = time.time()
        rx_data = usrp.recv_num_samps(
            num_samps, args.freq, args.rate, args.channels, args.gain, streamer=rx_streamer
        )
        print(
            "Received ",
            colored(rx_data.size, "green"),
            " samples from Rx data from snapshot number #",
            colored(i, "green"),
        )

        # get USRP coerced values only once if we running the same config
        if i == 0:
            args.coerced_rx_rate = usrp.get_rx_rate()
            args.coerced_rx_freq = usrp.get_rx_freq()
            args.coerced_rx_gain = usrp.get_rx_gain()
            args.coerced_rx_bandwidth = usrp.get_rx_bandwidth()
            args.coerced_rx_lo_source = usrp.get_rx_lo_source()  # Not part of meta data

        # Get time stamp
        time_stamp_micro_sec = datetime.now().strftime("%Y_%m_%d-%H_%M_%S_%f")
        time_stamp_milli_sec = time_stamp_micro_sec[:-3]

        # write recorded data to file
        rx_data_file_name = "rx_data_record_" + time_stamp_milli_sec
        dataset_filename = rx_data_file_name + ".sigmf-data"
        dataset_file_path = os.path.join(args.rx_recorded_data_path, dataset_filename)
        print(dataset_file_path)
        rx_data.tofile(dataset_file_path)

        # Write data into files with the given format
        # create sigmf metadata
        meta = SigMFFile(
            data_file=dataset_file_path,  # extension is optional
            global_info={
                SigMFFile.DATATYPE_KEY: "cf32_le",  # get_data_type_str(rx_data) - 'cf64_le' is not supported yet
                SigMFFile.SAMPLE_RATE_KEY: args.coerced_rx_rate,  # args.rate,
                SigMFFile.NUM_CHANNELS_KEY: len(args.channels),
                SigMFFile.AUTHOR_KEY: "Abdo Gaber",
                SigMFFile.DESCRIPTION_KEY: "5GNR Waveform: NR, FR1, DL, FDD, 64-QAM, 30 kHz SCS, 20 MHz bandwidth, TM3.1",
                SigMFFile.RECORDER_KEY: "UHD Python API",
                SigMFFile.LICENSE_KEY: "NI RF Data Recording API",
                SigMFFile.HW_KEY: hw_type,
                SigMFFile.DATASET_KEY: dataset_filename,
                SigMFFile.VERSION_KEY: sigmf.__version__,
            },
        )

        # Create a capture key at time index 0
        meta.add_capture(
            0,  # Sample Start
            metadata={
                SigMFFile.FREQUENCY_KEY: args.coerced_rx_freq,  # args.freq,
                SigMFFile.DATETIME_KEY: dt.datetime.utcnow().isoformat() + "Z",
                "capture_details": {
                    "acquisition_bandwidth": args.coerced_rx_bandwidth,
                    "gain": args.coerced_rx_gain,
                },
            },
        )

        # get waveform config
        txs_info = {}
        signal_detail = {
            "standard": "5GNR_FR1",
            "frequency_range": "FR1",
            "link_direction": "Downlink",
            "test_model": "TM3.1",
            "bandwidth": "20000000",
            "subcarrier_spacing": "30000",
            "duplexing": "FDD",
            "multiplexing": "OFDM",
            "multiple_access": "OFDM",
            "modulation": "64-QAM",
        }

        signal_emitter = {
            "seid": 1,  # Unique ID of the emitter
            "hw": "USRP X310",
            "hw_subtype": "UBX-120",
            "manufacturer": "NI",
            "frequency": "20000000000",
            "sample_rate": "30720000",
            "bandwidth": "160000000",
            "gain_tx": "20",
            "clock_reference": "internal",
        }

        txs_info["Tx_0"] = {
            "signal:detail": signal_detail,
            "signal:emitter": signal_emitter,
        }

        # get channel info
        channel_info = {
            "attenuation": "33",
        }
        # get rx info
        rx_info = {
            "seid": seid,
            "hw_subtype": hw_subtype,
            "manufacturer": "NI",
            "clock_reference": args.reference,
            "bandwidth": max_RF_bandwidth,
        }
        # Add an annotation
        meta.add_annotation(
            0,  # Sample Start
            num_samps,  # Sample count
            metadata={
                SigMFFile.FLO_KEY: args.coerced_rx_freq
                - args.coerced_rx_rate / 2,  # args.freq - args.rate / 2,
                SigMFFile.FHI_KEY: args.coerced_rx_freq
                + args.coerced_rx_rate / 2,  # args.freq + args.rate / 2,
                SigMFFile.LABEL_KEY: "5GNR_FR1",
                SigMFFile.COMMENT_KEY: "USRP RX IQ DATA CAPTURE",
                "num_tx_signals": "uknown",
                "system_components:transmitter": txs_info,
                "system_components:channel": channel_info,
                "system_components:receiver": rx_info,
            },
        )

        # check for mistakes
        assert meta.validate()

        ## Write Meta Data to file
        dataset_meta_filename = rx_data_file_name + ".sigmf-meta"
        dataset_meta_file_path = os.path.join(args.rx_recorded_data_path, dataset_meta_filename)
        meta.tofile(dataset_meta_file_path)  # extension is optional
        print(dataset_meta_file_path)

        end_time = time.time()
        time_elapsed = end_time - start_time
        time_elapsed_ms = int(time_elapsed * 1000)
        print(
            "Elapsed time of getting rx samples and writing data and meta data files:",
            colored(time_elapsed_ms, "yellow"),
            "ms",
        )
        print("")


if __name__ == "__main__":
    main()
