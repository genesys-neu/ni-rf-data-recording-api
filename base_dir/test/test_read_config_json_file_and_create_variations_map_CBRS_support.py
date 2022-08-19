##! Data Recording API
#
# Copyright 2022 NI Dresden
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Pre-requests: Install UHD with Python API enabled
#
from optparse import Values
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
        ## Read general parameter set from json config file
        file_path = (
            "C:/Abdo.Gaber/python/lti-6g-sw_new/lti-6g-sw/data-recording-tools/uhd/uhd-python-api/"
        )
        with open(os.path.join(file_path, config_file_name), "r") as file:
            config = json.load(file)
        self.config = config

    # Calculate the range
    def drange(start, stop, step):
        r = start
        while r <= stop:
            yield r
            r += step

    # Change parameter from range to list
    def change_parameter_range_to_list(parameter_config):
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
        return parameter_config

    # Create variation map
    class CreateVariationsMap:
        """Top-level RFDataRecorder class"""

        def __init__(self, config):
            ## Read varaitions
            variations = config["variations"]

            # Initialize parameters
            # define dictionay inclusing all parameters
            variations_dict = {}
            # number of TX and RX USRPs
            num_tx_usrps = 0
            num_rx_usrps = 0

            ## Create list of variations for every parameter
            for index, value in enumerate(variations):
                device_config = variations[index]
                # check if the given set of parameters are a set for a device or common parameters
                # For a device
                if "DeviceName" in device_config.keys():
                    if device_config["RFmode"] == "Tx":
                        # get device ID
                        num_tx_usrps = num_tx_usrps + 1
                        device_id = device_config["RFmode"] + str(num_tx_usrps)
                    elif device_config["RFmode"] == "Rx":
                        # get device ID
                        num_rx_usrps = num_rx_usrps + 1
                        device_id = device_config["RFmode"] + str(num_rx_usrps)
                    else:
                        raise Exception("ERROR: Unkown RF Mode of given device")
                    # get device arguements
                    variations_dict[device_id + "_args"] = [
                        "type=" + device_config["type"] + ",addr=" + device_config["IPaddress"]
                    ]

                    # get device config parameters
                    parameters = device_config["Parameters"]
                    for index, value in enumerate(parameters):
                        parameter_config = parameters[index]
                        if parameter_config["SeqType"] == "range":
                            parameter_config = RFDataRecorderAPI.change_parameter_range_to_list(
                                parameter_config
                            )
                            variations_dict[
                                device_id + "_" + parameter_config["Parameter"]
                            ] = parameter_config["Values"]
                        elif parameter_config["SeqType"] == "list":
                            variations_dict[
                                device_id + "_" + parameter_config["Parameter"]
                            ] = parameter_config["Values"]
                        elif parameter_config["SeqType"] == "single":
                            variations_dict[device_id + "_" + parameter_config["Parameter"]] = [
                                parameter_config["Values"]
                            ]
                        else:
                            raise Exception(
                                "ERROR: The supported variations options are: range, list, and single"
                            )
                # For a common TX or RX parameter
                else:
                    parameter_config = device_config
                    if parameter_config["SeqType"] == "range":
                        parameter_config = RFDataRecorderAPI.change_parameter_range_to_list(
                            parameter_config
                        )
                        variations_dict[parameter_config["Parameter"]] = parameter_config["Values"]
                    elif parameter_config["SeqType"] == "list":
                        variations_dict[parameter_config["Parameter"]] = parameter_config["Values"]
                    elif parameter_config["SeqType"] == "single":
                        variations_dict[device_id + "_" + parameter_config["Parameter"]] = [
                            parameter_config["Values"]
                        ]
                    else:
                        raise Exception(
                            "ERROR: The supported variations options are: range and list"
                        )

            ## Create a data frame based on all variations
            # Do the cross product for all possible values
            # First: Initialize data frame using the first parameter
            variations_list = list(variations_dict.items())
            parameter_config = variations_list[0]
            parameter, value = parameter_config
            variations_product = DataFrame({parameter: value})
            for i in range(len(variations_list) - 1):
                parameter_config = variations_list[i + 1]
                parameter, value = parameter_config
                data_frame_i = DataFrame({parameter: value})
                variations_product = variations_product.merge(data_frame_i, how="cross")
            # Store variations product in self class
            self.variations_product = variations_product

            # Print resulting variations product on terminal
            print("Resulting variations cross product: ")
            print(variations_product)
            print("Number of variations: ", len(variations_product))

            ## Get general config
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

            # Store number of TX USRPs
            data_frame_tx = DataFrame({"num_tx_usrps": [num_tx_usrps]})
            general_config_dic = general_config_dic.merge(data_frame_tx, how="cross")  #
            # Store number of RX USRPs
            data_frame_rx = DataFrame({"num_rx_usrps": [num_rx_usrps]})
            general_config_dic = general_config_dic.merge(data_frame_rx, how="cross")

            # Store general variations product in self class
            self.general_config_dic = general_config_dic

            # Print resulting variations product on terminal
            print("General Config Parameters: ")
            print(general_config_dic)

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


def main():

    ## Get RF Data Collection API Configuration
    config_file_name = "config_rf_data_recording_api_new.json"

    # Create RF data recording API class and load Config
    print("Load RF Data recorder config ...")
    rf_data_recording_api = RFDataRecorderAPI(config_file_name)
    # print(rf_data_recording_api.config)
    ## Create all configuration variations - cross product
    print("Create configuration variations ...")
    variations_map = rf_data_recording_api.CreateVariationsMap(rf_data_recording_api.config)
    print("")


if __name__ == "__main__":
    sys.exit(not main())
