#
# Copyright 2022 National Instruments Corporation
#
# SPDX-License-Identifier: MIT
#
"""
RF Data Recording API Configuration Interface
"""
# Description:
#   The configuration interface reads the configuration file and creates the variation map by doing a cross product over all possible values. Each TX and RX has own list of parameters. Some TX parameters are common for all Tx USRPs, and they are listed under common transmitters config section. The resulting variation map has four sections:
# 	    - General configuration
# 	    - TX USRP configuration
# 	    - Common Tx USRPs configuration
# 	    - RX USRP configuration
#
import os
import yaml
import json
import pandas as pd
import functools
from pathlib import Path
# import other functions
from lib import data_format_conversion_lib
from lib import rf_data_recording_api_def

# Read config file
def read_config_files(rf_data_acq_config_file: str):
    """
    Reads rf data acq config file of RF Data Collection API
    """
    name, extension = os.path.splitext(rf_data_acq_config_file)
    dir_path = os.path.dirname(__file__)
    src_path = os.path.split(dir_path)[0] 
    # read general parameter set from yaml config file
    if extension == ".yaml":
        with open(os.path.join(src_path, rf_data_acq_config_file), "r") as file:
            rf_data_acq_config = yaml.load(file, Loader=yaml.Loader)
    # Read general parameter set from json config file
    elif extension == ".json":
        with open(os.path.join(src_path, rf_data_acq_config_file), "r") as file:
            rf_data_acq_config = json.load(file)
    else:
        raise Exception(f"Unsupported file format '{extension}'.")

    return rf_data_acq_config, extension


# Check whether dict of config is filled at all
def check_config_dict(config_dict):
    if bool(config_dict):
        for key, value in config_dict.items():
            if not value:
                raise Exception(f"Config field '{key}' is not filled!")


# Calculate the range
def drange(start, stop, step):
    r = start
    i = 0
    while r <= stop:
        yield r
        r += step
        i = i + 1
        if i == 10:
            break


# Change parameter from range to list
def change_parameter_range_to_list(parameter_config):
    parameter_config["SeqType"] = "list"
    parameter_values_range = parameter_config["Values"]
    parameter_values_list = list(
        drange(
            parameter_values_range[0],
            parameter_values_range[1],
            parameter_values_range[2],
        )
    )
    parameter_config["Values"] = parameter_values_list

    return parameter_config


# Get device config dictionary
def get_device_variations_config_dict(device_variations_config_dict, RFmode, variations_dict):
    ## Create list of variations for every parameter
    num_usrps = 0
    if device_variations_config_dict:
        for index, value in enumerate(device_variations_config_dict):
            device_config = device_variations_config_dict[index]
            # check whether device config dict is filled at all
            check_config_dict(device_config)

            if device_config["RFmode"] == RFmode:
                # get device ID
                num_usrps = num_usrps + 1
                device_id = device_config["RFmode"] + str(num_usrps)
            else:
                raise Exception("ERROR: Unkown RF Mode of given device or wrong config")

            # get device arguements
            variations_dict[device_id + "_args"] = [
                "type=" + device_config["type"] + ",addr=" + device_config["IPaddress"]
            ]

            # get device config parameters
            parameters = device_config["Parameters"]
            for key, parameter_config in parameters.items():
                key_id = device_id + "_" + key
                # get parmeter values, change to list if values given in range or single
                if parameter_config["SeqType"] == "range":
                    parameter_config = change_parameter_range_to_list(parameter_config)
                    target_value = parameter_config["Values"]
                elif parameter_config["SeqType"] == "list":
                    target_value = parameter_config["Values"]
                elif parameter_config["SeqType"] == "single":
                    target_value = [parameter_config["Values"]]
                else:
                    raise Exception(
                        "ERROR: The supported variations options are: range, list, and single"
                    )
                variations_dict[key_id] = target_value

    return variations_dict, num_usrps


# Create variation map
class CreateVariationsMap:
    """Top-level Create variation map class"""

    def __init__(self, rf_data_acq_config):
        # Save RF data collection config as it is in the given file in the class
        self.rf_data_acq_config = rf_data_acq_config
        # ---------------------------------------
        ## Get Variations config
        # --------------------------------------
        # Initialize parameters
        # define dictionay inclusing all parameters
        variations_dict = {}

        # ---------------------------------------
        ## Get Transmitters config
        # --------------------------------------
        ## Read transmitters variations
        tx_variations_config_dict = rf_data_acq_config["transmitters_config"]
        RFmode_tx = rf_data_recording_api_def.RFDataRecorderAPI.RFmode[0]
        variations_dict, num_tx_usrps = get_device_variations_config_dict(
            tx_variations_config_dict, RFmode_tx, variations_dict
        )

        # ---------------------------------------
        ## Get Transmitters Common config
        # --------------------------------------
        ## Read common transmitters variations
        if num_tx_usrps != 0:
            tx_common_config_dict = rf_data_acq_config["common_transmitters_config"]
            ## Create list of variations for every parameter
            for key, parameter_config in tx_common_config_dict.items():
                # get parmeter values, change to list if values given in range or single
                if parameter_config["SeqType"] == "range":
                    parameter_config = change_parameter_range_to_list(parameter_config)
                    target_value = parameter_config["Values"]
                elif parameter_config["SeqType"] == "list":
                    target_value = parameter_config["Values"]
                elif parameter_config["SeqType"] == "single":
                    target_value = [parameter_config["Values"]]
                else:
                    raise Exception(
                        "ERROR: The supported variations options are: range, list, and single"
                    )
                variations_dict[key] = target_value

        # ---------------------------------------
        ## Get Receivers config
        # --------------------------------------
        ## Read Receivers variations
        rx_variations_config_dict = rf_data_acq_config["receivers_config"]
        RFmode_rx = rf_data_recording_api_def.RFDataRecorderAPI.RFmode[1]
        variations_dict, num_rx_usrps = get_device_variations_config_dict(
            rx_variations_config_dict, RFmode_rx, variations_dict
        )
        # ---------------------------------------
        ## Get Variations map by doing a Cross-product
        # --------------------------------------
        # First, create a data frame for all parameters
        # preallocate list to collect pandas data frames
        variations_list = list(variations_dict.items())
        parameter_config = variations_list[0]
        parameter, value = parameter_config
        variations_product = pd.DataFrame({parameter: value})
        for i in range(len(variations_list) - 1):
            parameter_config = variations_list[i + 1]
            parameter, value = parameter_config
            data_frame_i = pd.DataFrame({parameter: value})
            variations_product = variations_product.merge(data_frame_i, how="cross")

        # Store variations product in self class
        self.variations_product = variations_product

        # ---------------------------------------
        ## Get general config
        # --------------------------------------
        general_config_dict = rf_data_acq_config["general_config"]
        # check whether dict for general_config is filled at all
        check_config_dict(general_config_dict)

        # preallocate list to collect pandas data frames
        general_config_frames = []
        for key, value in general_config_dict.items():
            # collect all data frames in a list
            general_config_frames.append(pd.DataFrame({key: [value]}))
        # Store number of TX USRPs
        data_frame_tx = pd.DataFrame({"num_tx_usrps": [num_tx_usrps]})
        general_config_frames.append(data_frame_tx)
        # Store number of RX USRPs
        data_frame_rx = pd.DataFrame({"num_rx_usrps": [num_rx_usrps]})
        general_config_frames.append(data_frame_rx)

        # Derive API Operation Mode: Tx-only, Rx-only, Tx-Rx
        if num_tx_usrps > 0 and num_rx_usrps > 0:  # Tx-Rx mode
            API_operation_mode = rf_data_recording_api_def.RFDataRecorderAPI.API_operation_modes[2]
        elif num_tx_usrps == 0:  # Rx only mode
            API_operation_mode = rf_data_recording_api_def.RFDataRecorderAPI.API_operation_modes[1]
        elif num_rx_usrps == 0:  # Tx only mode
            API_operation_mode = rf_data_recording_api_def.RFDataRecorderAPI.API_operation_modes[0]
        else:
            raise Exception(
                f"Unknown API operation mode, num Tx stations:{num_tx_usrps}, num Rx stations:{num_rx_usrps}."
            )
        data_frame_op_mode = pd.DataFrame({"API_operation_mode": [API_operation_mode]})
        general_config_frames.append(data_frame_op_mode)

        # create cross-product of all single data frames
        general_config = functools.reduce(
            lambda df1, df2: pd.merge(df1, df2, how="cross"), general_config_frames
        )

        # Store general config in self class
        self.general_config = general_config


def generate_rf_data_recording_configs(rf_data_acq_config_file: str):
    """
    Reads config file and generates list of configurations as a cross-product of specified systematic variation
    ranges.
    """
    # Read RF Data collection API YAML config file
    rf_data_acq_config, extension = read_config_files(rf_data_acq_config_file)

    enable_console_logging = data_format_conversion_lib.str2bool(
        rf_data_acq_config["general_config"]["enable_console_logging"]
    )

    # Print RF Data Collection Config as it is given in the config file
    if enable_console_logging:
        print("RF Data Collection Configuration based on the Config File: ")
        print("File format: ", extension)
        print(rf_data_acq_config)

    # Create the variation map
    variations_map = CreateVariationsMap(rf_data_acq_config)

    # Print resulting variations product on terminal
    if enable_console_logging:
        print("Resulting variations cross product: ")
        print(variations_map.variations_product)
        print("Number of variations: ", len(variations_map.variations_product))
        print("")

        # Print resulting general_config terminal
        print("General Config Parameters: ")
        print(variations_map.general_config)
        print("")

    return variations_map
