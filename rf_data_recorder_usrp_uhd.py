##! Data Recording API
# NI
#
# Pre-requests: Install UHD with Python API enabled
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
"""
Write RX samples to file using UHD Python API
"""

import argparse
import numpy as np
import uhd

# To write Data to sigmf file
import sigmf
import datetime as dt
from sigmf import SigMFFile
from sigmf.utils import get_data_type_str

# To save to specific path
import os

# To meausre elapsed time
import time


def parse_args():
    """Parse the command line arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--args", default="", type=str)
    parser.add_argument("-o", "--output-file", type=str, required=True)
    parser.add_argument("-f", "--freq", type=float, required=True)
    parser.add_argument("-r", "--rate", default=1e6, type=float)
    parser.add_argument("-d", "--duration", default=5.0, type=float)
    parser.add_argument("-c", "--channels", default=0, nargs="+", type=int)
    parser.add_argument("-g", "--gain", type=int, default=10)
    parser.add_argument(
        "-n",
        "--numpy",
        default=False,
        action="store_true",
        help="Save output file in NumPy format (default: No)",
    )
    parser.add_argument("-nr", "--nrecords", type=int, default=1)
    return parser.parse_args()


def main():
    """Get RX samples"""
    args = parse_args()
    usrp = uhd.usrp.MultiUSRP(args.args)
    num_samps = int(np.ceil(args.duration * args.rate))
    if not isinstance(args.channels, list):
        args.channels = [args.channels]
    for i in range(args.nrecords):
        start_time = time.time()
        rx_data = usrp.recv_num_samps(num_samps, args.freq, args.rate, args.channels, args.gain)
        end_time = time.time()
        time_elapsed = end_time - start_time
        print("Elapsed time of getting rx samples", time_elapsed)
        print("Received Rx Data of snapshot number: ", i)
        # print(data)

        ## Write RX samples to file in cf32_le
        start_time = time.time()
        dataset_filename = "rx_data_" + str(i) + ".sigmf-data"
        data_output_file = os.path.join(args.output_file, dataset_filename)
        # data_output_file  = os.path.join(os.path.expanduser('~'), args.output_file, 'rx_data_' + str(i) + '.sigmf-data')
        rx_data.tofile(data_output_file)
        print(data_output_file)

        ## create the metadata
        meta = SigMFFile(
            data_file=data_output_file,  # extension is optional
            global_info={
                SigMFFile.DATATYPE_KEY: "cf32_le",  # in this case, 'cf32_le'
                SigMFFile.SAMPLE_RATE_KEY: args.rate,
                SigMFFile.NUM_CHANNELS_KEY: len(args.channels),
                SigMFFile.AUTHOR_KEY: "Abdo Gaber abdo.gaber@ni.com",
                SigMFFile.DESCRIPTION_KEY: "5GNR Waveform: NR, FR1, DL, FDD, 64-QAM, 30 kHz SCS, 20 MHz bandwidth, TM3.1",
                SigMFFile.RECORDER_KEY: "UHD Python API",
                SigMFFile.LICENSE_KEY: "URL to the license document",
                SigMFFile.HW_KEY: "USRP X310",
                # SigMFFile.DATASET_KEY: dataset_filename,
                SigMFFile.VERSION_KEY: sigmf.__version__,
            },
        )

        # create a capture key at time index 0
        meta.add_capture(
            0,  # Sample Start
            metadata={
                SigMFFile.FREQUENCY_KEY: args.freq,
                SigMFFile.DATETIME_KEY: dt.datetime.utcnow().isoformat() + "Z",
            },
        )

        # add an annotation
        meta.add_annotation(
            0,  # Sample Start
            num_samps,  # Sample count
            metadata={
                SigMFFile.FLO_KEY: args.freq - args.rate / 2,
                SigMFFile.FHI_KEY: args.freq + args.rate / 2,
                SigMFFile.COMMENT_KEY: dataset_filename,
                SigMFFile.LABEL_KEY: "5GNR_FR1",
                SigMFFile.COMMENT_KEY: "",
                "signal:detail": {
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
        # meta_output_file  = os.path.join(os.path.expanduser('~'), args.output_file, 'rx_data_' + str(i) + '.sigmf-meta')
        meta.tofile(meta_output_file)  # extension is optional
        end_time = time.time()
        time_elapsed = end_time - start_time
        print("Elapsed time of writing data and meta data files", time_elapsed)
        print(meta_output_file)


if __name__ == "__main__":
    main()
