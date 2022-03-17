##! Data Recording API
# NI
#
# Pre-requests: Install UHD with Python API enabled
#

import argparse
from pickle import FALSE, TRUE
from unicodedata import name
import numpy as np
import uhd

# To create USRP streamer
import uhd

# To write Data to sigmf file
import sigmf
import datetime as dt
from sigmf import SigMFFile
from sigmf.utils import get_data_type_str

# To save to specific path
import os
from pathlib import Path

# To measure elapsed time
import time

# To print colours
import sys
from termcolor import colored, cprint


def parse_args():
    """Parse the command line arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a", "--args", default="type=x300,addr=192.168.40.2,master_clock_rate=184.32e6", type=str
    )
    parser.add_argument(
        "-o",
        "--output-file",
        default=(Path(__file__).parent / "../../../../recorded-data").resolve(),
        type=str,
    )
    parser.add_argument("-f", "--freq", default=2e9, type=float, help="RF center frequency in Hz")
    parser.add_argument("-r", "--rate", default=30.72e6, type=float, help="rate of radio block")
    parser.add_argument("-d", "--duration", default=10e-3, type=float)
    parser.add_argument(
        "-c", "--channels", default=0, nargs="+", type=int, help="radio channel to use"
    )
    parser.add_argument("-g", "--gain", default=30, type=float, help="gain for the RF chain")
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

    # get process api arguments
    args = parse_args()

    # define number of samples to fetch
    num_samps = int(np.ceil(args.duration * args.rate))

    if not isinstance(args.channels, list):
        args.channels = [args.channels]

    # initialize usrp
    print("Initialize usrp ...")
    usrp = uhd.usrp.MultiUSRP(args.args)
    usrp_info = usrp.get_usrp_rx_info()
    print(usrp_info)
    usrp_serial_number = usrp_info["mboard_serial"]

    # set up the stream
    print("Setup the stream ...")
    st_args = uhd.usrp.StreamArgs("fc32", "sc16")
    st_args.channels = args.channels  # If you're only using one channel, then this is simply [0]
    rx_streamer = usrp.get_rx_stream(st_args)

    # set TX/RX port as receive port
    for kk in args.channels:
        usrp.set_rx_antenna(args.antenna, kk)

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

        # write recorded data to file
        dataset_filename = "rx_data_" + str(i) + ".sigmf-data"
        dataset_folder = os.path.join(args.output_file, dataset_filename)
        print(dataset_folder)
        rx_data.tofile(dataset_folder)

        # get USRP coerced values only once if we running the same config
        if i == 0:
            coerced_rx_rate = usrp.get_rx_rate()
            coerced_rx_freq = usrp.get_rx_freq()
            coerced_rx_gain = usrp.get_rx_gain()
            coerced_rx_bandwidth = usrp.get_rx_bandwidth()
            coerced_rx_lo_source = usrp.get_rx_lo_source()  # Not part of meta data

        # create sigmf metadata
        meta = SigMFFile(
            data_file=dataset_folder,  # extension is optional
            global_info={
                SigMFFile.DATATYPE_KEY: "cf32_le",  # get_data_type_str(rx_data) - 'cf64_le' is not supported yet
                SigMFFile.SAMPLE_RATE_KEY: coerced_rx_rate,  # args.rate,
                SigMFFile.NUM_CHANNELS_KEY: len(args.channels),
                SigMFFile.AUTHOR_KEY: "Abdo Gaber, abdo.gaber@ni.com",
                SigMFFile.DESCRIPTION_KEY: "5GNR Waveform: NR, FR1, DL, FDD, 64-QAM, 30 kHz SCS, 20 MHz bandwidth, TM3.1",
                SigMFFile.RECORDER_KEY: "UHD Python API",
                SigMFFile.LICENSE_KEY: "URL to the license document",
                SigMFFile.HW_KEY: "USRP " + usrp_info["mboard_id"],
                SigMFFile.DATASET_KEY: dataset_filename,
                SigMFFile.VERSION_KEY: sigmf.__version__,
            },
        )

        # create a capture key at time index 0
        meta.add_capture(
            0,  # Sample Start
            metadata={
                SigMFFile.FREQUENCY_KEY: coerced_rx_freq,  # args.freq,
                SigMFFile.DATETIME_KEY: dt.datetime.utcnow().isoformat() + "Z",
                "capture_details": {
                    "acquisition_bandwidth": coerced_rx_bandwidth,
                    "gain": coerced_rx_gain,
                    "attenuation": 30,
                    "source_file": "rf_data_recorder_usrp_uhd.py",  # RF IQ recording filename that was used to create the file
                },
            },
        )

        # add an annotation
        meta.add_annotation(
            0,  # Sample Start
            num_samps,  # Sample count
            metadata={
                SigMFFile.FLO_KEY: coerced_rx_freq
                - coerced_rx_rate / 2,  # args.freq - args.rate / 2,
                SigMFFile.FHI_KEY: coerced_rx_freq
                + coerced_rx_rate / 2,  # args.freq + args.rate / 2,
                SigMFFile.LABEL_KEY: "5GNR_FR1",
                SigMFFile.COMMENT_KEY: "USRP RX IQ DATA CAPTURE",
                SigMFFile.GENERATOR_KEY: usrp_serial_number,
                "signal:detail": {
                    "data_type": rx_data.dtype.name,
                    "system": "5GNR Release 15",
                    "standard": "5GNR_FR1",
                    "duplexing": "FDD",
                    "multiplexing": "ofdm",
                    "multiple_access": "ofdm",
                    "type": "digital",
                    "mod_class": "qam",
                    "carrier_variant": "single_carrier",
                    "order": 64,
                    "bandwidth": 2000000.0,
                    "channel": 78,  # channel number of the signal within the communication system.
                },
                "signal:emitter": {
                    "seid": 1,  # Unique ID of the emitter
                    "manufacturer": "NI",
                    "power_tx": 8.0,
                },
            },
        )

        # check for mistakes
        assert meta.validate()

        ## Write Meta Data to file
        meta_output_file = os.path.join(args.output_file, "rx_data_" + str(i) + ".sigmf-meta")
        meta.tofile(meta_output_file)  # extension is optional
        end_time = time.time()
        time_elapsed = end_time - start_time
        time_elapsed_ms = int(time_elapsed * 1000)
        print(
            "Elapsed time of getting rx samples and writing data and meta data files:",
            colored(time_elapsed_ms, "yellow"),
            "ms",
        )
        print(meta_output_file)
        print("")


if __name__ == "__main__":
    main()
