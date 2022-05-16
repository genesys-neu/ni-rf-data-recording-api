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
import pandas
import uhd
import math

# to read tdms properties from rfws file
# https://www.datacamp.com/community/tutorials/python-xml-elementtree
from re import X
import xml.etree.cElementTree as ET

# to read csv file of matlab waveform created using IEEE reference generator
import csv
import re

# to read tdms file
from nptdms import TdmsFile
from nptdms import tdms


class RFDataRecorderAPI:
    """Top-level RF Data Recorder API class"""

    def __init__(self, config_file_name):
        ## Read general parameter set from json config file
        with open(os.path.join(os.path.dirname(__file__), config_file_name), "r") as file:
            config = json.load(file)
        self.config = config

    # Calculate the range
    def drange(start, stop, step):
        r = start
        while r <= stop:
            yield r
            r += step

    # Create variation map
    class CreateVariationsMap:
        """Variation map class"""

        def __init__(self, config):
            ## Read varaitions
            variations = config["variations"]

            ## Create list of variarations for every parameter
            for index, value in enumerate(variations):
                parameter_config = variations[index]
                # Change parameter values from range, if given, to list
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
                elif parameter_config["SeqType"] != "list":
                    print("ERROR: The supported variations options are: range and list")
                    return

            ## Create a data frame based on all variations
            # Do the cross product for all possible values
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
            # "path to TDMS/mat/... file, type = str ",
            self.waveform_path = iteration_general_config["tx_waveform_path"]
            # "possible values: tdms, matlab_ieee, type = str ",
            self.tx_waveform_format = iteration_general_config["tx_waveform_format"]
            # "rate_source: pssoible options
            # (user_defined: given in variations section),
            # (waveform_config: read from waverform config properties)"
            self.rate_source = iteration_general_config["rate_source"]
            # "to store USRP SN, type = str "
            self.usrp_serial_number = ""
            # Define dictionary for tx  wavform config
            waveform_config = {}
            self.waveform_config = waveform_config

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
            self.rx_recorded_data_saving_format = iteration_general_config[
                "rx_recorded_data_saving_format"
            ]
            # initialize rx parameters
            self.num_rx_samps = 0
            self.coerced_rx_rate = 0.0
            self.coerced_rx_freq = 0.0
            self.coerced_rx_gain = 0.0
            self.coerced_rx_bandwidth = 0.0
            self.coerced_rx_lo_source = 0.0
            self.usrp_mboard_id = ""
            self.usrp_serial_number = ""

    ## Find proper clock rate
    def calculate_master_clock_rate(self, requested_rate, args_in):
        def round_up_to_even(f):
            return math.ceil(f / 2.0) * 2

        # There are two master clock rates (MCR) supported on the X300 and X310: 200.0 MHz and 184.32 MHz.
        # The achievable sampling rates is by using an even decimation factor
        master_clock_rate_x310 = [200e6, 184.32e6]

        # Calculate the ratio between MCR and requested samling rate
        ratio_frac = [x / requested_rate for x in master_clock_rate_x310]
        # Change to integer
        ratio_integ = [round(x) for x in ratio_frac]
        # Find the higher even number
        ratio_even = []
        for index, value in enumerate(ratio_frac):
            value = ratio_integ[index]
            if value < 1:
                ratio_even.append(2)
            elif value < 2:
                ratio_even.append(0)
            else:
                ratio_even.append(round_up_to_even(value))
        # Calculate the deviation
        ratio_dev = []
        for index, value in enumerate(ratio_even):
            value1 = ratio_even[index]
            value2 = ratio_frac[index]
            ratio_dev.append(abs(value1 - value2))
        # Find the best MCR for the requested rate
        pos = ratio_dev.index(min(ratio_dev))
        master_clock_rate_config = master_clock_rate_x310[pos]
        if master_clock_rate_config == 184.32e6:
            args_out = args_in + ",master_clock_rate=184.32e6"
        else:
            args_out = args_in + ",master_clock_rate=200e6"
        return args_out

    ## Get serial numbers of TX USRPs -  This extra step is a workaround
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

    ## Get TX USRP id of the running USRP from the list of TX USRPs
    def handle_tx_usrp_serial_number(self, tx_usrp_serial_numbers_list, tx_args):
        for index, value in enumerate(tx_usrp_serial_numbers_list):
            given_tx_arg = tx_usrp_serial_numbers_list[index]
            if tx_args == given_tx_arg[0]:
                usrp_serial_number = given_tx_arg[1]
                break
        return usrp_serial_number

    ## Read tdms waveform data config from rfws file
    def read_tdms_waveform_config(path, file):
        folder_path = (Path(__file__).parent / path).resolve()
        # The tdms waveform config file is saved with the same name of waveform but it has .rfws extenstion
        file_path = str(folder_path) + "/" + file + ".rfws"

        # change numerical string with k, M, or G to float number
        def freq_string_to_float(x):
            if "k" in x:
                x_str = x.replace("k", "000")
            elif "M" in x:
                x_str = x.replace("M", "000000")
            elif "G" in x:
                x_str = x.replace("G", "000000000")
            else:
                x_str = x
            return float(x_str)

        # reading the rfws file
        xmlDoc = ET.parse(file_path)
        root = xmlDoc.getroot()

        # XPath expressiion searching all elements recursively starting from root './/*'
        # that have an attribute 'name' with the value e.i. 'Bandwidth (Hz)'
        # returns a list, either iterate over the list or select list element zero [0] if you expect only one hit
        # more sophisticated expressions are possible
        waveform_config = {}

        # get standard
        factory = root.findall(".//*[@name='factory']")
        factory = factory[0].text
        waveform_config["Standard"] = factory

        # get bandwidth
        bwElements = root.findall(".//*[@name='Bandwidth (Hz)']")
        bw = bwElements[0].text
        waveform_config["Bandwidth"] = freq_string_to_float(bw)

        # get freqeuncy range
        freqRanges = root.findall(".//*[@name='Frequency Range']")
        FR = freqRanges[0].text
        waveform_config["Freqeuncy_Range"] = FR

        # get link direction
        link_directions = root.findall(".//*[@name='Link Direction']")
        link_direction = link_directions[0].text
        waveform_config["link_direction"] = link_direction

        # get number of frames
        n_frames = root.findall(".//*[@name='Number of Frames']")
        n_frames = n_frames[0].text
        waveform_config["n_frames"] = n_frames

        if waveform_config["link_direction"] == "Downlink":
            # check if test model is enabled
            dl_ch_config_modes = root.findall(".//*[@name='DL Ch Configuration Mode']")
            dl_ch_config_mode = dl_ch_config_modes[0].text
            if dl_ch_config_mode == "Test Model":
                # get DL test model
                dl_test_models = root.findall(".//*[@name='DL Test Model']")
                dl_test_model = dl_test_models[0].text
                waveform_config["dl_test_model"] = dl_test_model

                # get modulation type
                mod = root.findall(".//*[@name='DL Test Model Modulation Type']")
                # for PDSCH, select first catch, for PUSCH select second catch
                mod = mod[0].text
                waveform_config["MOD"] = mod

                # get DL duplex
                dl_duplex = root.findall(".//*[@name='DL Test Model Duplex Scheme']")
                dl_duplex = dl_duplex[0].text
                waveform_config["duplexing"] = dl_duplex

            elif dl_ch_config_mode == "User Defined":
                # get DL test model
                waveform_config["dl_test_model"] = dl_ch_config_mode

                # get modulation type
                mod = root.findall(".//*[@name='Modulation Type']")
                # for PDSCH, select first catch, for PUSCH select second catch
                mod = mod[0].text
                waveform_config["MOD"] = mod

                # get DL duplex
                waveform_config["duplexing"] = dl_ch_config_mode
        elif waveform_config["link_direction"] == "Uplink":
            # get DL test model, no test model for Uplink
            waveform_config["dl_test_model"] = "User Defined"

            # get modulation type
            mod = root.findall(".//*[@name='Modulation Type']")
            # for PDSCH, select first catch, for PUSCH select second catch
            mod = mod[1].text
            waveform_config["MOD"] = mod

            # get DL duplex
            waveform_config["duplexing"] = "User Defined"
        else:
            raise Exception("ERROR: Unkown or not supported link direction")

        # get subcarrier spacing
        scs = root.findall(".//*[@name='Subcarrier Spacing (Hz)']")
        scs = scs[0].text
        waveform_config["SCS"] = scs

        # get CC index
        cc_index = root.findall(".//*[@name='CarrierCCIndex']")
        cc_index = cc_index[0].text
        waveform_config["CarrierCCIndex"] = cc_index

        # get ssb info
        ssb_config_set = root.findall(".//*[@name='Configuration Set']")
        ssb_config_set = ssb_config_set[0].text
        waveform_config["ssb_config_set"] = ssb_config_set

        # get ssb periodicity
        ssb_periodicity = root.findall(".//*[@name='Periodicity']")
        ssb_periodicity = ssb_periodicity[0].text
        waveform_config["ssb_periodicity"] = ssb_periodicity

        # multiplexing
        waveform_config["multiplexing"] = "OFDM"
        # multiple access
        waveform_config["multiple_access"] = ""

        # get rate
        tx_data_complex, waveform_IQ_rate = RFDataRecorderAPI.read_tdms_waveform_data(path, file)
        waveform_config["rate"] = waveform_IQ_rate

        return waveform_config

    ## Read waveform data config in matlab format for IEEE waveform generator
    def read_mat_ieee_waveform_config(path, file):
        folder_path = (Path(__file__).parent / path / str(file)).resolve()
        file_path = str(folder_path) + "/cfg.csv"

        with open(file_path, "r") as file_p:
            csvreader = csv.reader(file_p)
            header = next(csvreader)
            rows = header
            for row in csvreader:
                rows.append(row)

        cfg_list = []
        for row in rows:
            if row[0][0] != "#":
                cfg_list.append(row)

        pattern = r";"
        cfg_list_split = []
        for row in cfg_list:
            cfg_list_split.append(re.split(pattern, row[0]))

        cfg_dict = {}
        header = cfg_list_split[0]
        values = cfg_list_split[1]

        for index in range(len(header)):
            cfg_dict[header[index]] = values[index]

        cfg_dict["BW"] = float(cfg_dict["BW_str"]) * 1e6
        if cfg_dict["mods"] == "1":
            cfg_dict["mods"] = "BPSK"
        elif cfg_dict["mods"] == "2":
            cfg_dict["mods"] = "QPSK"
        elif cfg_dict["mods"] == "4":
            cfg_dict["mods"] = "16QAM"
        elif cfg_dict["mods"] == "6":
            cfg_dict["mods"] = "64QAM"
        elif cfg_dict["mods"] == "8":
            cfg_dict["mods"] = "256QAM"
        else:
            print("ERROR: Not supported modulation scheme order")
            cfg_dict["mods"] = ""

        # create harmonized dictionary
        waveform_config = {}
        waveform_config["Standard"] = file
        waveform_config["Bandwidth"] = cfg_dict["BW"]
        waveform_config["MCS"] = cfg_dict["mcs"]
        waveform_config["code_rate"] = cfg_dict["crate"]
        waveform_config["MOD"] = cfg_dict["mods"]
        waveform_config["SCS"] = ""
        waveform_config["MAC_frame_type"] = cfg_dict["format"]
        waveform_config["PSDU_length_bytes"] = cfg_dict["PSDU_length"]
        # multiplexing
        waveform_config["multiplexing"] = "OFDM"
        # multiple access
        waveform_config["multiple_access"] = ""
        # get rate  -->  in wifi sampling rate = bandwidth
        waveform_config["rate"] = waveform_config["Bandwidth"]

        return waveform_config

    # read waveform config
    def read_waveform_config(self, tx_data_recording_api_config):
        if tx_data_recording_api_config.tx_waveform_format == "tdms":
            tx_data_recording_api_config.waveform_config = (
                RFDataRecorderAPI.read_tdms_waveform_config(
                    tx_data_recording_api_config.waveform_path,
                    tx_data_recording_api_config.waveform_file_name,
                )
            )
        elif tx_data_recording_api_config.tx_waveform_format == "matlab_ieee":
            tx_data_recording_api_config.waveform_config = (
                RFDataRecorderAPI.read_mat_ieee_waveform_config(
                    tx_data_recording_api_config.waveform_path,
                    tx_data_recording_api_config.waveform_file_name,
                )
            )
        else:
            waveform_config = {}
            waveform_config["Standard"] = "unknown"
            tx_data_recording_api_config.waveform_config = waveform_config
        return tx_data_recording_api_config

    ## Read waveform data in TDSM format
    def read_tdms_waveform_data(path, file):

        # Open the file
        tdms_file = TdmsFile.read(str(path) + str(file) + ".tdms")
        # get all channels
        group = tdms_file["waveforms"]
        # get channel dat
        channel = ""
        if "Channel 0" in group:
            channel = group["Channel 0"]
        elif "segment0/channel0" in group:
            channel = group["segment0/channel0"]
        if not channel:
            raise Exception("ERROR: Unkown channel name of a given TDMS Waveform")

        wavform_IQ_rate = channel.properties["NI_RF_IQRate"]

        tx_data_float = channel[:]
        tx_data_complex = tx_data_float[::2] + 1j * tx_data_float[1::2]
        return tx_data_complex, wavform_IQ_rate

    ## Update rate based on user selection given by user or from waveform config
    def update_rate(self, tx_data_recording_api_config, rx_data_recording_api_config):
        if tx_data_recording_api_config.rate_source == "waveform_config":
            tx_data_recording_api_config.bandwidth = tx_data_recording_api_config.waveform_config["Bandwidth"]
            tx_data_recording_api_config.rate = tx_data_recording_api_config.waveform_config["rate"]
            rx_data_recording_api_config.rate = tx_data_recording_api_config.waveform_config["rate"]

        return tx_data_recording_api_config, rx_data_recording_api_config
    
    # print iteration config
    def print_iteration_config(self,iteration_config, iteration_general_config, tx_data_recording_api_config):
        import warnings
        warnings.filterwarnings('ignore')
        iteration_config["rate"] = str(tx_data_recording_api_config.rate)
        iteration_config["tx_bandwidth"] = str(tx_data_recording_api_config.bandwidth)
        warnings.filterwarnings('default')
        print("Iteration config: ")
        print(iteration_config)
        print("Iteration general config: ")
        print(iteration_general_config)
