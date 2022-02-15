#! Data Recording API
# NI
#
# Pre-requests: UHD with Python API enabled
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
        rx_data = usrp.recv_num_samps(num_samps, args.freq, args.rate, args.channels, args.gain)
        print("Received Rx Data of snapshot number: ", i)

        # Combine real and imag in a vector as real[0], imag[0],real[1], imag[1]
        a = 0
        b = 0
        data = np.zeros(2 * num_samps, dtype="float32")
        for a in range(num_samps):
            data[b] = rx_data.real[args.channels, a]
            b = b + 1
            data[b] = rx_data.imag[args.channels, a]
            b = b + 1

        # Write RX samples to file
        # write those samples to file in rf32_le
        # data.tofile('rx_data' + str(i) + '.sigmf-data')
        data_output_file = os.path.join(args.output_file, "rx_data_" + str(i) + ".sigmf-data")
        # data_output_file  = os.path.join(os.path.expanduser('~'), args.output_file, 'rx_data_' + str(i) + '.sigmf-data')
        data.tofile(data_output_file)
        print(data_output_file)

        # Write Meta Data to file
        # create the metadata
        meta = SigMFFile(
            # data_file='rx_data_' + str(i) + '.sigmf-data', # extension is optional
            data_file=data_output_file,  # extension is optional
            global_info={
                SigMFFile.DATATYPE_KEY: "rf32_le",  # in this case, 'rf32_le'
                SigMFFile.SAMPLE_RATE_KEY: args.rate,
                SigMFFile.AUTHOR_KEY: "abdo.gaber@ni.com",
                SigMFFile.DESCRIPTION_KEY: "rx_data_" + str(i),
                SigMFFile.VERSION_KEY: sigmf.__version__,
            },
        )

        # create a capture key at time index 0
        meta.add_capture(
            0,
            metadata={
                SigMFFile.FREQUENCY_KEY: args.freq,
                SigMFFile.DATETIME_KEY: dt.datetime.utcnow().isoformat() + "Z",
            },
        )

        # add an annotation
        meta.add_annotation(
            0,
            num_samps,
            metadata={
                SigMFFile.FLO_KEY: args.freq - args.rate / 2,
                SigMFFile.FHI_KEY: args.freq + args.rate / 2,
                SigMFFile.COMMENT_KEY: "rx_data_" + str(i),
            },
        )

        # check for mistakes & write to disk
        assert meta.validate()

        # meta.tofile('rx_data' + str(i) + '.sigmf-meta') # extension is optional
        meta_output_file = os.path.join(args.output_file, "rx_data_" + str(i) + ".sigmf-meta")
        # meta_output_file  = os.path.join(os.path.expanduser('~'), args.output_file, 'rx_data_' + str(i) + '.sigmf-meta')
        meta.tofile(meta_output_file)  # extension is optional
        print(meta_output_file)


if __name__ == "__main__":
    main()
