##! Data Recording API
#
# Copyright 2022 NI Dresden
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Pre-requests: Install UHD with Python API enabled
#
import os
import json
from timeit import default_timer as timer
from pathlib import Path
from multiprocessing.sharedctypes import Value
from operator import index
import numpy as np
from pandas import DataFrame, merge
import uhd

class RFDataRecorderAPI:
    """Top-level RF Data Recorder API class"""

    def __init__(self, config_file_name):
        ## read general parameter set from json config file
        with open(os.path.join(os.path.dirname(__file__), config_file_name), "r") as file:
            config = json.load(file)
        self.config = config

    # calculate the range
    def drange(start, stop, step):
        r = start
        while r <= stop:
            yield r
            r += step

    # create variation map
    class CreateVariationsMap:
        """Variation map class"""

        def __init__(self, config):
            ## read varaitions
            variations = config["variations"]

            ## create list of variarations for every parameter
            for index, value in enumerate(variations):
                parameter_config = variations[index]
                # change parameter values from range, if given, to list
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
                elif  parameter_config["SeqType"] != "list":
                    print("ERROR: The supported variations options are: range and list")
                    return

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
            print("")

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
            print("")

    # Define TX Class for RF Data Reecording API Config Parameters
    class TxRFDataRecorderConfig:
        """Tx RFDataRecorder Config class"""

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
            # "to store USRP SN, type = str "
            self.usrp_serial_number = ""

    # Define RX Class for RX Config Parameters
    class RxRFDataRecorderConfig:
        """Rx RFDataRecorder Config class"""

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
            # "time duration of IQ data acquisition"
            self.duration = iteration_config["rx_duration"]
            # "number of snapshots from RX IQ data acquisition"
            self.nrecords = iteration_general_config["nrecords"]
            # "path to store captured rx data, type = str",
            self.rx_recorded_data_path = (
                Path(__file__).parent / iteration_general_config["rx_recorded_data_path"]
            ).resolve()
            # expected channel atteuntion, type = float"
            self.channel_attenuation = iteration_general_config["channel_attenuation"]
            # rx recorded data saving format, type = str, possible values "SigMF"
            self.rx_recorded_data_saving_format = iteration_general_config["rx_recorded_data_saving_format"]
            # initialize rx parameters
            self.num_rx_samps = 0 
            self.coerced_rx_rate = 0.0
            self.coerced_rx_freq = 0.0
            self.coerced_rx_gain = 0.0
            self.coerced_rx_bandwidth = 0.0
            self.coerced_rx_lo_source = 0.0
            self.usrp_mboard_id=""
            self.usrp_serial_number=""

    # find proper clock rate
    # There are two master clock rates (MCR) supported on the X300 and X310: 200.0 MHz and 184.32 MHz.
    def calculate_master_clock_rate(self, args_in):
        # we are focusing on 5G NR signals
        # x3100_rates = [200e6, 184.32e6]
        # Use master clock rates (MCR) of 184.32 MHz as a reference
        args_out = args_in + ",master_clock_rate=184.32e6"
        return args_out

    # get serial numbers of TX USRPs -  This extra step is a workaround
    # getting USRP SN is supported in Multi-USRP but not on RFNoC graph
    def get_usrp_serial_number(self):
        variations = self.config["variations"]
        for index, value in enumerate(variations):
            parameter_config = variations[index]
            # find tx args
            if parameter_config["Parameter"] == "tx_args":
                tx_args = parameter_config["Values"]
                break
        tx_usrp_serial_numbers_list = []
        for index, arg in enumerate(tx_args):
            usrp = uhd.usrp.MultiUSRP(arg)
            usrp_info = usrp.get_usrp_rx_info()
            print("TX USRP number ", index, " info:")
            print(usrp_info)
            tx_usrp_serial_number = usrp_info["mboard_serial"]
            tx_usrp_serial_numbers_list.append([arg, tx_usrp_serial_number])
        return tx_usrp_serial_numbers_list

    # get TX USRP id of the running USRP from the list of TX USRPs
    def handle_tx_usrp_serial_number(self, tx_usrp_serial_numbers_list, tx_args):
        for index, value in enumerate(tx_usrp_serial_numbers_list):
            given_tx_arg = tx_usrp_serial_numbers_list[index]
            if tx_args == given_tx_arg[0]:
                usrp_serial_number = given_tx_arg[1]
                break
        return usrp_serial_number
