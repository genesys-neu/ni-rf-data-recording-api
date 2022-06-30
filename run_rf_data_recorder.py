##! Data Recording API: RX
#
# Copyright 2022 NI Dresden
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Pre-requests: Install UHD with Python API enabled
#

from pickle import FALSE, TRUE
from unicodedata import name
import numpy as np
import uhd

# To save to specific path
import os
from pathlib import Path

# To measure elapsed time
import time

# To print colours
from termcolor import colored, cprint
import sync_settings

# import related functions
import write_rx_recorded_data_in_sigmf


def rf_data_recorder(rx_args, txs_args, rx_data_nbytes_que):
    """RX Data Recorder"""

    # Define number of samples to fetch
    rx_args.num_rx_samps = int(np.ceil(rx_args.duration * rx_args.rate))

    if not isinstance(rx_args.channels, list):
        rx_args.channels = [rx_args.channels]

    # Initialize usrp
    print("Initialize usrp ...")
    usrp = uhd.usrp.MultiUSRP(rx_args.args)
    usrp_info = usrp.get_usrp_rx_info()
    print("RX USRP info:")
    print(usrp_info)
    rx_args.usrp_mboard_serial = usrp_info["mboard_serial"]
    rx_args.usrp_mboard_id = usrp_info["mboard_id"]

    # Set up the stream
    print("Setup the stream ...")
    cpu_format = "fc32"
    wire_format = "sc16"
    st_args = uhd.usrp.StreamArgs(cpu_format, wire_format)
    st_args.channels = rx_args.channels  # If you're only using one channel, then this is simply [0]
    rx_streamer = usrp.get_rx_stream(st_args)

    # Set receive port (TX/RX or RX2)
    for index in rx_args.channels:
        usrp.set_rx_antenna(rx_args.antenna, index)

    # Wait to get a command to start RX data acquisition if TX is on TX mode already
    while sync_settings.start_rx_data_acquisition_called == False:
        time.sleep(0.1)  # sleep for 100ms

    # Run data recording loop over specified number of iterations
    print("Start fetching RX data from USRP...")

    rx_data_nbytes = 0.0
    for i in range(rx_args.nrecords):

        # Fetch data from usrp device
        start_time = time.time()
        rx_data = usrp.recv_num_samps(
            rx_args.num_rx_samps,
            rx_args.freq,
            rx_args.rate,
            rx_args.channels,
            rx_args.gain,
            streamer=rx_streamer,
        )
        print(
            "Received ",
            colored(rx_data.size, "green"),
            " samples from Rx data from snapshot number #",
            colored(i, "green"),
        )
        rx_data_nbytes = rx_data_nbytes + rx_data.nbytes

        # Get USRP coerced values only once
        # To reduce latency, the number of records is executed per each configuration
        if i == 0:
            rx_args.coerced_rx_rate = usrp.get_rx_rate()
            rx_args.coerced_rx_freq = usrp.get_rx_freq()
            rx_args.coerced_rx_gain = usrp.get_rx_gain()
            rx_args.coerced_rx_bandwidth = usrp.get_rx_bandwidth()
            rx_args.coerced_rx_lo_source = usrp.get_rx_lo_source()  # Not part of meta data yet

        # Write data into files with the given format
        if rx_args.rx_recorded_data_saving_format == "SigMF":
            write_rx_recorded_data_in_sigmf.write_rx_recorded_data_in_sigmf(
                rx_data, rx_args, txs_args
            )
        else:
            # Report error.
            raise Exception("ERROR: selected writing rx recorded data format is not supported")

        end_time = time.time()
        time_elapsed = end_time - start_time
        time_elapsed_ms = int(time_elapsed * 1000)
        print(
            "Elapsed time of getting rx samples and writing data and meta data files:",
            colored(time_elapsed_ms, "yellow"),
            "ms",
        )
    rx_data_nbytes_que.put(rx_data_nbytes)

    # Send command to TX thread to stop data transmission
    sync_settings.stop_tx_signal_called = True
