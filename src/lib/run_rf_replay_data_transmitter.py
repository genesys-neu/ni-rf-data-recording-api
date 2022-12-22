#
# Copyright 2022 National Instruments Corporation
#
# SPDX-License-Identifier: MIT
#
"""
TX Waveform Playback
"""
# Description:
#   Use for TX waveform playback. Given wavform can be in TDMS or MATLAB format
#
# Parameters:
#   Given from the top-level script based on the API configuration file
#
# Pre-requests: Install UHD with Python API enabled
#
import sys
import signal
import time
import argparse
import numpy as np
import uhd
from nptdms import TdmsFile
import scipy.io

# import other functions
from lib import read_waveform_data_interface
from lib import sync_settings

# string to boolean
def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


def rf_replay_data_transmitter(args):
    """
    Run Tx waveform playback
    """

    # Print help message
    print("UHD/RFNoC Replay samples from file ")
    print("This application uses the Replay block to playback data from a file to a radio")

    # ************************************************************************
    # Create device and block controls
    # ************************************************************************
    print("Creating the RFNoC graph with args: ", args.args)
    graph = uhd.rfnoc.RfnocGraph(args.args)
    # print("USRP Static connections:")
    # for edge in graph.enumerate_static_connections():
    #    print(edge.to_string())
    # print("")

    # Create handle for radio object
    available_radios = graph.find_blocks("Radio")
    print("Avaliable radios: ", len(available_radios))

    radio_ctrl_id = uhd.rfnoc.BlockID(0, "Radio", args.radio_id)
    radio_ctrl = uhd.rfnoc.RadioControl(graph.get_block(radio_ctrl_id))

    # Check if the replay block exists on this device
    replay_ctrl_id = uhd.rfnoc.BlockID(0, "Replay", args.replay_id)
    if graph.has_block(replay_ctrl_id) == False:
        print('Unable to find block "' + replay_ctrl_id + '"')
        return
    replay_ctrl = uhd.rfnoc.ReplayBlockControl(graph.get_block(replay_ctrl_id))

    # Check for a DUC connected to the radio
    duc_ctrl_id = uhd.rfnoc.BlockID(0, "DUC", args.duc_chan)
    duc_ctrl = uhd.rfnoc.DucBlockControl(graph.get_block(duc_ctrl_id))

    # Connect replay to radio
    uhd.rfnoc.connect_through_blocks(
        graph, replay_ctrl_id, args.replay_chan, radio_ctrl_id, args.radio_chan, False
    )

    print(f"Using Radio Block: {radio_ctrl_id}, channel {args.radio_chan}")
    print(f"Using Replay Block: {replay_ctrl_id}, channel {args.replay_chan}")
    print(f"Using DUC Block: {duc_ctrl_id}, channel {args.duc_chan}")
    print("")

    # ************************************************************************
    # * Set up streamer to Replay block and commit graph
    # ************************************************************************
    replay_ctrl.set_play_type("sc16", 0)
    replay_ctrl.set_record_type("sc16", 0)
    tx_md = uhd.types.TXMetadata()
    cpu_format = "fc32"
    wire_format = "sc16"
    num_ports = 1

    print("Setting up graph...")
    stream_args = uhd.usrp.StreamArgs(cpu_format, wire_format)
    tx_streamer = graph.create_tx_streamer(num_ports, stream_args)
    graph.connect(tx_streamer, 0, replay_ctrl.get_unique_id(), args.replay_chan)
    graph.commit()

    # ************************************************************************
    # * Set up radio
    # ************************************************************************
    print("")
    print("Setting up radio ...")

    # Set clock reference
    num_mboards = graph.get_num_mboards()
    print(f"Number of mboards: {num_mboards}")
    graph.get_mb_controller(0).set_clock_source(args.clock_reference)

    # Set the center frequency
    print(f"Requesting TX Freq: {(args.freq / 1e6)} MHz...")
    if str2bool(args.enable_lo_offset):
        if args.lo_offset > args.bandwidth / 2 and args.lo_offset < (
            (args.max_RF_bandwidth - args.bandwidth) / 2
        ):
            radio_ctrl.set_tx_frequency(args.freq + args.lo_offset, args.radio_chan)
            duc_ctrl.set_freq(-args.lo_offset, args.duc_chan)
        else:
            raise Exception(
                "ERROR: LO Freqeuncy offset is:",
                args.lo_offset,
                ". It should be greater than ",
                args.bandwidth / 2,
                " and less than ",
                (args.max_RF_bandwidth - args.bandwidth) / 2,
            )
    else:
        radio_ctrl.set_tx_frequency(args.freq, args.radio_chan)
    coerced_tx_freq = radio_ctrl.get_tx_frequency(args.radio_chan) 
    print(f"Actual TX Freq: {coerced_tx_freq/ 1e6}  MHz...")
    print(f"** TX Carrier Frequency Offset: {coerced_tx_freq - args.freq}  Hz...")

    # Set the sample rate
    print(f"Requesting TX Rate: {(args.rate / 1e6) } Msps...")
    duc_ctrl.set_input_rate(args.rate, args.duc_chan)
    coerced_tx_rate = duc_ctrl.get_input_rate(args.duc_chan)
    print(f"Actual TX Rate: {(coerced_tx_rate / 1e6)} Msps...")
    print(f"** TX Sampling Rate Offset: {coerced_tx_rate - args.rate}  Sample per second...")

    # Set the RF gain
    print(f"Requesting TX Gain: {args.gain} dB...")
    radio_ctrl.set_tx_gain(args.gain, args.radio_chan)
    coerced_tx_gain = radio_ctrl.get_tx_gain(args.radio_chan)
    print(f"Actual TX Gain: {coerced_tx_gain} dB...")

    # Set the analog front-end filter bandwidth
    print(f"Requesting TX Bandwidth: {(args.bandwidth / 1e6)} MHz...")
    radio_ctrl.set_tx_bandwidth(args.bandwidth, args.radio_chan)
    coerced_tx_bandwidth = radio_ctrl.get_tx_bandwidth(args.radio_chan)
    print(f"Actual TX Bandwidth: {coerced_tx_bandwidth / 1e6} MHz...")
    print("Note: Not all doughterboards support variable analog bandwidth")

    # Set the antenna
    print(f"Requesting TX Antenna: {(args.antenna)}")
    radio_ctrl.set_tx_antenna(args.antenna, args.radio_chan)
    print(f"Actual TX Antenna: {radio_ctrl.get_tx_antenna(args.radio_chan)}")

    # Allow for some setup time
    time.sleep(100e-3)

    # ************************************************************************
    # * Read the data to replay
    # ************************************************************************
    print("")
    print("Reading data to replay...")

    # Constants related to the Replay block
    replay_word_size = replay_ctrl.get_word_size()  # Size of words used by replay block
    print("Word size of Replay block: ", replay_word_size)
    # UHD do the job and set the sample size from Complex signed 64-bit is 32 bits per sample
    sample_size = 4

    # Read waveform based on waveform format
    if args.waveform_format == "tdms":  # args.file.endswith(".tdms"):
        tx_data_complex, waveform_IQ_rate = read_waveform_data_interface.read_waveform_data_tdms(
            args.waveform_path, args.waveform_file_name
        )
        if args.rate != waveform_IQ_rate:
            print("Note:The IQ Rate based on TDMS Waveform property should be: ", waveform_IQ_rate)
    elif args.waveform_format == "matlab_ieee":
        tx_data_complex = read_waveform_data_interface.read_waveform_data_matlab_ieee(
            args.waveform_path, args.waveform_file_name
        )
    elif args.waveform_format == "matlab":
        tx_data_complex = read_waveform_data_interface.read_waveform_data_matlab(
            args.waveform_path, args.waveform_file_name
        )
    else:
        raise Exception("ERROR: Unkown or not supported tx waveform format.")

    # Get the file size
    file_size = len(tx_data_complex) * sample_size

    # Calculate the number of 64-bit words and samples to replay
    words_to_replay = int(file_size / replay_word_size)  # bytes
    samples_to_replay = int(file_size / sample_size)  # bytes
    print("Max number of samples: ", tx_streamer.get_max_num_samps())
    print("Samples to replay: ", samples_to_replay)

    # Read data into np buffer, rounded down to number of words
    tx_data = np.tile(np.array(tx_data_complex, dtype=np.complex64), (num_ports, 1))

    # ************************************************************************
    # * Configure replay block
    # ***********************************************************************
    # Configure a buffer in the on-board memory at address 0 that's equal in
    # size to the file we want to play back (rounded down to a multiple of
    # 64-bit words). Note that it is allowed to playback a different size or
    # location from what was recorded.
    print("")
    print("Configuring replay block....")

    replay_buff_addr = 0
    replay_buff_size = int(samples_to_replay * sample_size)
    replay_ctrl.record(replay_buff_addr, replay_buff_size, args.replay_chan)

    # Display replay configuration
    print(
        f"Replay file size:      {replay_buff_size} bytes ({ words_to_replay} qwords, {samples_to_replay} samples)"
    )
    print(f"Record base address:0x {replay_ctrl.get_record_offset(args.replay_chan)}")
    print(f"Record buffer size:    {replay_ctrl.get_record_size(args.replay_chan)}  bytes")
    print(f"Record fullness:       {replay_ctrl.get_record_fullness(args.replay_chan)} bytes")

    # Restart record buffer repeatedly until no new data appears on the Replay
    # block's input. This will flush any data that was buffered on the input.
    print("Emptying record buffer...")
    fullness = 1
    while fullness > 0:
        replay_ctrl.record_restart(args.replay_chan)
        # Make sure the record buffer doesn't start to fill again
        start_time = time.time()
        seconds_elapsed = 0
        while seconds_elapsed < 0.250:
            fullness = replay_ctrl.get_record_fullness(args.replay_chan)
            end_time = time.time()
            seconds_elapsed = end_time - start_time
            if fullness != 0:
                break

    print(f"Record fullness:     {replay_ctrl.get_record_fullness(args.replay_chan)}  bytes")

    # ************************************************************************
    # * Send data to replay (== record the data)
    # ************************************************************************
    print("")
    print("Sending data to be recorded...")

    tx_md.start_of_burst = True
    tx_md.end_of_burst = True

    # We use a very big timeout here, any network buffering issue etc. is not
    # a problem for this application, and we want to upload all the data in one
    # send() call.
    # num_tx_samps = tx_streamer.send(tx_data, samples_to_replay, tx_md, 5.0)
    # Note: if samples_to_replay is used in the above function, we got error
    print(tx_data.size)
    num_tx_samps = tx_streamer.send(tx_data, tx_md, 5.0)
    if num_tx_samps != samples_to_replay:
        print(f"ERROR: Unable to send {samples_to_replay} samples (sent {num_tx_samps} )")

    # ************************************************************************
    # * Wait for data to be stored in on-board memory
    # ************************************************************************
    print("Waiting for recording to complete...")
    while replay_ctrl.get_record_fullness(args.replay_chan) < replay_buff_size:
        print(f"Record fullness: {replay_ctrl.get_record_fullness(args.replay_chan)}")
        time.sleep(0.05)  # sleep for 50ms

    print(f"Record fullness: {replay_ctrl.get_record_fullness(args.replay_chan)} bytes")

    # ************************************************************************
    # * Start replay of data
    # ***********************************************************************
    print("")
    print("Starting Replay of Data ...")

    # Replay the entire buffer over and over
    repeat = True
    print(f"Issuing replay command for {samples_to_replay} samples in continuous mode...")
    time_spec = uhd.types.TimeSpec(0.0)
    replay_ctrl.play(replay_buff_addr, replay_buff_size, args.replay_chan, time_spec, repeat)

    # Send a command to start RX data aquestions
    sync_settings.start_rx_data_acquisition_called = True
    while sync_settings.stop_tx_signal_called == False:
        time.sleep(0.05)  # sleep for 50ms

    print("Stopping replay...")
    replay_ctrl.stop(args.replay_chan)
    print("Letting device settle...")
    time.sleep(0.05)  # sleep for 50ms
