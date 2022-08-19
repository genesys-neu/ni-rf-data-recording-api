##! Data Recording API
#
# Copyright 2022 NI Dresden
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Pre-requests: Install UHD with Python API enabled
#
import sys
import os
import json
import time
from timeit import default_timer as timer
from pathlib import Path

# importing the threading module
import threading
from multiprocessing.sharedctypes import Value
from operator import index
import numpy as np
import itertools
from pandas import DataFrame, merge
import math

# import related functions
# import run_rf_replay_data_transmitter
# import run_rf_data_recorder
# import sync_settings


class RFDataRecorderAPI:
    """Top-level RF Data Recoorder API class"""

    def __init__(self, config_file_name):
        # read general parameter set from json config file
        file_path = os.path.split(os.path.dirname(__file__))
        with open(os.path.join(file_path[0], config_file_name), "r") as file:
            config = json.load(file)
        self.config = config

    # calculate the range
    def drange(start, stop, step):
        r = start
        while r <= stop:
            yield r
            r += step

    # Create variation map
    class CreateVariationsMap:
        """Top-level RFDataRecorder class"""

        def __init__(self, config):
            ## read varaitions
            variations = config["variations"]

            ## create list of variarations for every parameter
            for index, value in enumerate(variations):
                parameter_config = variations[index]
                # change parameter values from range if given to list
                if parameter_config["SeqType"] == "range":
                    parameter_config["SeqType"] = "list"
                    parameter_values_range = parameter_config["Values"]
                    parameter_values_list = list(
                        RFDataRecorderAPI.drange(
                            parameter_values_range[0],
                            parameter_values_range[1],
                            parameter_values_range[2],
                        )
                    )
                    parameter_config["Values"] = parameter_values_list
                    variations[index] = parameter_config

            ## create a data frame based on all variations
            # do the cross product for all possible values
            # initialize data frame using the first parameter
            parameter_config = variations[0]
            variations_product = DataFrame(
                {parameter_config["Parameter"]: parameter_config["Values"]}
            )
            for i in range(len(variations) - 1):
                parameter_config = variations[i + 1]
                data_frame_i = DataFrame(
                    {parameter_config["Parameter"]: parameter_config["Values"]}
                )
                variations_product = variations_product.merge(data_frame_i, how="cross")
            print("Resulting variations cross product: ")
            print(variations_product)
            print("Number of variations: ", len(variations_product))
            self.variations_product = variations_product

            ## get general config
            general_config = config["general_config"]
            parameter_config = general_config[0]
            general_config_dic = DataFrame(
                {parameter_config["Parameter"]: [parameter_config["Value"]]}
            )
            for i in range(len(general_config) - 1):
                parameter_config = general_config[i + 1]
                data_frame_i = DataFrame(
                    {parameter_config["Parameter"]: [parameter_config["Value"]]}
                )
                general_config_dic = general_config_dic.merge(data_frame_i, how="cross")
            print("General Config Parameters: ")
            print(general_config_dic)
            self.general_config_dic = general_config_dic

    # Define Class for RF Data Reecording API Config Parameters
    class TxRFDataRecorderConfig:
        """Top-level RFDataRecorder class"""

        def __init__(self, iteration_config, iteration_general_config):
            # ============= TX Config parameters =============
            # Device args to use when connecting to the USRP, type=str",
            self.args = iteration_config["tx_args"]
            # "RF center frequency in Hz, type = float ",
            self.freq = iteration_config["freq"]
            # "rate of radio block, type = float ",
            self.rate = iteration_config["rate"]
            # "gain for the RF chain, type = float",
            self.gain = iteration_config["tx_gain"]
            # "antenna selection, type = str",
            self.antenna = iteration_config["tx_antenna"]
            # "analog front-end filter bandwidth in Hz, type = float",
            self.bandwidth = iteration_config["tx_bandwidth"]
            # "tdms file name, type = str ",
            self.waveform_file_name = iteration_config["tx_waveform_file_name"]
            # "reference source (internal, external, gpsdo, type = str",
            self.reference = iteration_config["tx_reference"]
            # "radio block to use (e.g., 0 or 1), type = int",
            self.radio_id = iteration_config["tx_radio_id"]
            # "radio channel to use, type = int",
            self.radio_chan = iteration_config["tx_radio_chan"]
            # "replay block to use (e.g., 0 or 1), type = int",
            self.replay_id = iteration_config["tx_replay_id"]
            # "replay channel to use, type = int ",
            self.replay_chan = iteration_config["tx_replay_chan"]
            # "duc channel to use, type = int ",
            self.duc_chan = iteration_config["tx_duc_chan"]
            # "path to TDMS file, type = str ",
            self.waveform_path = iteration_general_config["tx_waveform_path"]
            # "number of samples to play (0 for infinite) and based on the number of samples in the loaded waveform, type = str",
            # "Code is not ready to send a specific number of samples, it sends the whole waveform",
            self.nsamps = 0

    # Define Class for RX Config Parameters
    class RxRFDataRecorderConfig:
        """Top-level RX RFDataRecorder class"""

        def __init__(self, iteration_config, iteration_general_config):
            # ============= RX Config parameters =============
            # Device args to use when connecting to the USRP, type=str",
            self.args = iteration_config["rx_args"]
            # "RF center frequency in Hz, type = float ",
            self.freq = iteration_config["freq"]
            # "rate of radio block, type = float ",
            self.rate = iteration_config["rate"]
            # "radio channel to use, type = int",
            self.channels = iteration_config["rx_channels"]
            # "antenna selection, type = str",
            self.antenna = iteration_config["rx_antenna"]
            # "gain for the RF chain, type = float",
            self.gain = iteration_config["rx_gain"]
            # "reference source (internal, external, gpsdo, type = str",
            self.reference = iteration_config["rx_reference"]
            # "time duration of IQ data acquestion"
            self.duration = iteration_config["rx_duration"]
            # "number of snapshots from RX IQ data aquestion"
            self.repeat = iteration_general_config["nrecords"]
            # path to store captured rx data
            self.output_path = (
                Path(__file__).parent / iteration_general_config["rx_recorded_data_path"]
            ).resolve()

    def calculate_master_clocl_rate(data_recording_api_config):
        # we are focusing on 5G NR signals
        # x3100_rates = [200e6, 184.32e6]
        # Use master clock rates (MCR) of 184.32 MHz as a reference
        data_recording_api_config.args = (
            data_recording_api_config.args + ",master_clock_rate=184.32e6"
        )
        return data_recording_api_config


def main():

    ## Get RF Data Collection API Configuration
    print("Load RF Data recorder config ...")
    config_file_name = "config_rf_data_recording_api.json"
    rf_data_recorder_api = RFDataRecorderAPI(config_file_name)

    ## Create all configuration variations
    print("Create configuration variations ...")
    variations_map = rf_data_recorder_api.CreateVariationsMap(rf_data_recorder_api.config)

    for i in range(len(variations_map.variations_product)):
        print("Variation Number: ", i)
        ##  initlize sync settings
        # sync_settings.init()
        # print("Sync Status: ", sync_settings.start_rx_data_acquisition_called, " ", sync_settings.stop_tx_signal_called)

        ## get TX and RX RF Data Recorder Config
        iteration_config = variations_map.variations_product.iloc[i]
        iteration_general_config = variations_map.general_config_dic.iloc[0]
        print("Iteration config: ")
        print(iteration_config)
        print("Iteration general config: ")
        print(iteration_general_config)

        ## Create TX and RX RF Config classes
        tx_data_recording_api_config = RFDataRecorderAPI.TxRFDataRecorderConfig(
            iteration_config, iteration_general_config
        )
        rx_data_recording_api_config = RFDataRecorderAPI.RxRFDataRecorderConfig(
            iteration_config, iteration_general_config
        )

        # calculate USRP master clockrate based on given rate
        tx_data_recording_api_config = RFDataRecorderAPI.calculate_master_clocl_rate(
            tx_data_recording_api_config
        )
        rx_data_recording_api_config = RFDataRecorderAPI.calculate_master_clocl_rate(
            rx_data_recording_api_config
        )


if __name__ == "__main__":
    sys.exit(not main())
