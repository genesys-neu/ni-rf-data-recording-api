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
#   Look to parse the command line arguments
#
#   Pre-requests: Install UHD with Python API enabled
#

import sys
import signal
import time
import argparse
import numpy as np

# from sympy import true
import uhd
from nptdms import TdmsFile
import scipy.io

# import other functions
from lib import read_waveform_data_interface

stop_tx_signal_called = False

# Ctrl+C handler
def signal_handler(sig, frame):
    global stop_tx_signal_called
    print("Exiting . . .")
    stop_tx_signal_called = True


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


# ************************************************************************
#    * Set up the program options
# ***********************************************************************/
def parse_args():
    """
    Return parsed command line args
    """
    parser = argparse.ArgumentParser(
        description="Run the Replay block by recording to the USRP's memory and "
        "playback the data"
    )
    parser.add_argument(
        "-a",
        "--args",
        default="type=x300,addr=192.168.40.2,master_clock_rate=184.32e6",
        type=str,
        help="Device args to use when connecting to the USRP.",
    )
    parser.add_argument(
        "-tx", "--tx_args", default="", type=str, help="Block args for the transmit radio"
    )
    parser.add_argument(
        "--radio_id",
        "-rai",
        default=0,
        nargs="+",
        type=int,
        help="radio block to use (e.g., 0 or 1).",
    )
    parser.add_argument(
        "--radio_chan", "-rac", default=0, nargs="+", type=int, help="radio channel to use"
    )
    parser.add_argument(
        "--replay_id",
        "-rpi",
        default=0,
        nargs="+",
        type=int,
        help="replay block to use (e.g., 0 or 1)",
    )
    parser.add_argument(
        "--replay_chan", "-rpc", default=0, nargs="+", type=int, help="replay channel to use"
    )
    parser.add_argument(
        "--duc_chan", "-duc", default=0, nargs="+", type=int, help="duc channel to use"
    )
    parser.add_argument(
        "--nsamps",
        "-ns",
        default=0,
        nargs="+",
        type=int,
        help="number of samples to play (0 for infinite)",
    )
    parser.add_argument(
        "-p",
        "--path",
        default=("waveforms/nr/"),
        type=str,
        help="path to waveform file",
    )
    parser.add_argument(
        "-fl",
        "--file",
        default=("NR_FR1_DL_FDD_SISO_BW-20MHz_CC-1_SCS-30kHz_Mod-64QAM_OFDM_TM3.1"),
        type=str,
        help="waveform file name or a folder name without extension",
    )
    parser.add_argument(
        "-wft",
        "--waveform_format",
        default=("tdms"),
        type=str,
        help="possible values: tdms, matlab, matlab_ieee",
    )
    parser.add_argument("-f", "--freq", default=3.6e9, type=float, help="RF center frequency in Hz")
    parser.add_argument("-loo", "--lo_offset", default=20e6, type=float, help="LO offset in Hz")
    parser.add_argument(
        "-enable_loo",
        "--enable_lo_offset",
        type=str2bool,
        nargs="?",
        const=True,
        default=False,
        help="Enable LO offset True or false",
    )
    parser.add_argument("-r", "--rate", default=30.72e6, type=float, help="rate of radio block")
    parser.add_argument("-g", "--gain", default=30, type=float, help="gain for the RF chain")
    parser.add_argument("-ant", "--antenna", default="TX/RX", type=str, help="antenna selection")
    parser.add_argument(
        "-bw",
        "--bandwidth",
        default=100e6,
        type=float,
        help="analog front-end filter bandwidth in Hz",
    )
    parser.add_argument(
        "-ref",
        "--reference",
        default="internal",
        type=str,
        help="clock reference source (internal, external, gpsdo)",
    )
    args = parser.parse_args()
    return args


def main():
    """
    Run Tx waveform playback
    """
    args = parse_args()

    # Print help message
    print("UHD/RFNoC Replay samples from file ")
    print("This application uses the Replay block to playback data from a file to ")
    print("a radio")

    # ************************************************************************
    # Create device and block controls
    # ************************************************************************
    print("Creating the RFNoC graph with args: ", args)
    graph = uhd.rfnoc.RfnocGraph(args.args)
    print("USRP Static connections:")
    for edge in graph.enumerate_static_connections():
        print(edge.to_string())
    print("")

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

    # Connect DUC to radio
    graph.connect(duc_ctrl_id, args.duc_chan, radio_ctrl_id, args.radio_chan, False)

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
    wire_format = "sc16"
    cpu_format = "fc32"
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
    graph.get_mb_controller(0).set_clock_source(args.reference)

    # Set the center frequency
    print(f"Requesting TX Freq: {(args.freq / 1e6)} MHz...")
    if args.enable_lo_offset:
        radio_ctrl.set_tx_frequency(args.freq + args.lo_offset, args.radio_chan)
        duc_ctrl.set_freq(-args.lo_offset, args.duc_chan)
        print(
            "Note: LO Freqeuncy offset is:",
            args.lo_offset,
            ". It should be greater than Signal BW /2 and less than (max_RF_bandwidth - Signal BW)/2",
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
    time.sleep(0.2)

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
            args.path, args.file
        )
        if args.rate != waveform_IQ_rate:
            print("Note:The IQ Rate based on TDMS Waveform property should be: ", waveform_IQ_rate)
    elif args.waveform_format == "matlab_ieee":
        tx_data_complex = read_waveform_data_interface.read_waveform_data_matlab_ieee(
            args.path, args.file
        )
    elif args.waveform_format == "matlab":
        tx_data_complex = read_waveform_data_interface.read_waveform_data_matlab(
            args.path, args.file
        )
    else:
        raise Exception("ERROR: Unkown or not supported tx waveform format")

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
        print(f"ERROR: Unable to send {samples_to_replay} samples sent ({num_tx_samps} )")

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

    if args.nsamps <= 0:
        # Replay the entire buffer over and over
        repeat = True
        print(f"Issuing replay command for {samples_to_replay} samples in continuous mode...")
        time_spec = uhd.types.TimeSpec(0.0)
        replay_ctrl.play(replay_buff_addr, replay_buff_size, args.replay_chan, time_spec, repeat)
        # ** Wait until user says to stop **
        # Setup SIGINT handler (Ctrl+C)
        signal.signal(signal.SIGINT, signal_handler)
        print("Press Ctrl+C to stop RF streaming")
        while stop_tx_signal_called == False:
            time.sleep(0.1)  # sleep for 100ms
        # Remove SIGINT handler
        # signal.signal(signal.SIGINT, signal_dfl)
        print("Stopping replay...")
        replay_ctrl.stop(args.replay_chan)
        print("Letting device settle...")
        time.sleep(0.5)
    else:
        # Replay nsamps, wrapping back to the start of the buffer if nsamps is
        # larger than the buffer size.
        print("ERROR: Code is not ready to play a specific number of samples")
        return


if __name__ == "__main__":
    sys.exit(not main())
