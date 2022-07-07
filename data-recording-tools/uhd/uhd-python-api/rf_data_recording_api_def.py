##! Data Recording API
#
# Copyright 2022 NI Dresden
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Pre-requests: Install UHD with Python API enabled
#
import os
import queue
import yaml
import signal

# to read csv file of matlab waveform created using IEEE reference generator
import csv

# from timeit import default_timer as timer
from pathlib import Path
import pandas as pd
import uhd
import math

# to read tdms properties from rfws file
# https://www.datacamp.com/community/tutorials/python-xml-elementtree
from re import X
import xml.etree.cElementTree as ET

# to read tdms file
from nptdms import TdmsFile

# from nptdms import tdms
import time

# importing the threading module
import threading

# import related functions
import run_rf_replay_data_transmitter
import run_rf_data_recorder
import sync_settings
import rf_data_recording_config_interface


class RFDataRecorderAPI:
    """Top-level RF Data Recorder API class"""

    def __init__(self, rf_data_acq_config_file):
        # read general parameter set from config file
        variations_map = rf_data_recording_config_interface.generate_rf_data_recording_configs(
            rf_data_acq_config_file
        )

        # Store them in the class
        self.variations_map = variations_map

    # Modulation schemes: lookup table as a constant dictionary:
    modulation_schemes = {"1": "BPSK", "2": "QPSK", "4": "16QAM", "6": "64QAM", "8": "256QAM"}
    RFmode = ["Tx", "Rx"]
    API_operation_modes = ["Tx-only", "Rx-only", "Tx-Rx"]

    # Load Waveform Config dictionary
    def initialize_waveform_config(default_waveform_config_file):
        with open(
            os.path.join(os.path.dirname(__file__), default_waveform_config_file), "r"
        ) as file:
            default_waveform_config = yaml.load(file, Loader=yaml.Loader)

        return default_waveform_config

    # string to boolean
    def str2bool(v):
        if isinstance(v, bool):
            return v
        if v.lower() in ("yes", "true", "t", "y", "1"):
            return True
        elif v.lower() in ("no", "false", "f", "n", "0"):
            return False
        else:
            raise Exception("ERROR: Boolean value expected.")

    # Change numerical string with k, M, or G to float number
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

    # Define TX Class for RF Data Reecording API Config Parameters
    class TxRFDataRecorderConfig:
        """Tx RFDataRecorder Config class"""

        def __init__(self, iteration_config, general_config, idx):
            # ============= TX Config parameters =============
            tx_id = RFDataRecorderAPI.RFmode[0] + str(idx)
            # Device args to use when connecting to the USRP, type=str",
            self.args = iteration_config[tx_id + "_args"]
            # "RF center frequency in Hz, type = float ",
            self.freq = iteration_config[tx_id + "_freq"]
            # lo_offset: type=float, help="LO offset in Hz")
            self.lo_offset = iteration_config[tx_id + "_lo_offset"]
            # enable_lo_offset: type=str2bool, Enable LO offset True or false")
            self.enable_lo_offset = iteration_config[tx_id + "_enable_lo_offset"]
            # "rate of radio block, type = float ",
            self.rate = iteration_config[tx_id + "_rate"]
            # "rate_source: pssoible options
            # (user_defined: given in variations section),
            # (waveform_config: read from waverform config properties)"
            self.rate_source = iteration_config[tx_id + "_rate_source"]
            # "gain for the RF chain, type = float",
            self.gain = iteration_config[tx_id + "_gain"]
            # "antenna selection, type = str",
            self.antenna = iteration_config[tx_id + "_antenna"]
            # "analog front-end filter bandwidth in Hz, type = float",
            self.bandwidth = iteration_config[tx_id + "_bandwidth"]
            # "tdms file name, type = str ",
            self.waveform_file_name = iteration_config[tx_id + "_waveform_file_name"]
            # "path to TDMS/mat/... file, type = str ",
            self.waveform_path = iteration_config[tx_id + "_waveform_path"]
            # "possible values: tdms, matlab_ieee, type = str ",
            self.waveform_format = iteration_config[tx_id + "_waveform_format"]
            # "clock reference source (internal, external, gpsdo, type = str",
            self.clock_reference = iteration_config["tx_clock_reference"]
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
            # "Hardware type, i.e. for USRP: USRP mboard ID (X310, or ....)
            self.hw_type = iteration_config[tx_id + "_hw_type"]
            # "Hardware subtype, i.e. for USRP: daughter board type (UBX-160, CBX-120)
            self.hw_subtype = iteration_config[tx_id + "_hw_subtype"]
            # "Hardware serial number, i.e. for USRP: mboard serial number
            self.seid = iteration_config[tx_id + "_seid"]
            # "HW RF maximum supported bandwidth
            self.max_RF_bandwidth = iteration_config[tx_id + "_max_RF_bandwidth"]
            # Define dictionary for tx wavform config
            waveform_config = {}
            self.waveform_config = waveform_config

    # Define RX Class for RX Config Parameters
    class RxRFDataRecorderConfig:
        """Rx RFDataRecorder Config class"""

        def __init__(self, iteration_config, general_config, idx):
            # ============= RX Config parameters =============
            rx_id = RFDataRecorderAPI.RFmode[1] + str(idx)
            # Device args to use when connecting to the USRP, type=str",
            self.args = iteration_config[rx_id + "_args"]
            # "RF center frequency in Hz, type = float ",
            self.freq = iteration_config[rx_id + "_freq"]
            # "rate of radio block, type = float ",
            self.rate = iteration_config[rx_id + "_rate"]
            # "rate_source: pssoible options
            # (user_defined: given in variations section),
            # (waveform_config: read from waverform config properties)"
            self.rate_source = iteration_config[rx_id + "_rate_source"]
            # "gain for the RF chain, type = float",
            self.gain = iteration_config[rx_id + "_gain"]
            # "rx bandwidth in Hz, type = float",
            self.bandwidth = iteration_config[rx_id + "_bandwidth"]
            # "radio channel to use, type = int",
            self.channels = iteration_config[rx_id + "_channels"]
            # "antenna selection, type = str",
            self.antenna = iteration_config[rx_id + "_antenna"]
            # "clock reference source (internal, external, gpsdo, type = str",
            self.clock_reference = iteration_config[rx_id + "_clock_reference"]
            # "time duration of IQ data acquisition"
            self.duration = iteration_config[rx_id + "_duration"]
            # "number of snapshots from RX IQ data acquisition"
            self.nrecords = general_config["nrecords"]
            # "path to store captured rx data, type = str",
            self.rx_recorded_data_path = (
                Path(__file__).parent / general_config["rx_recorded_data_path"]
            ).resolve()
            # rx recorded data saving format, type = str, possible values "SigMF"
            self.rx_recorded_data_saving_format = general_config["rx_recorded_data_saving_format"]
            # "Hardware type, i.e. for USRP: USRP mboard ID (X310, or ....)
            self.hw_type = iteration_config[rx_id + "_hw_type"]
            # "Hardware subtype, i.e. for USRP: daughter board type (UBX-160, CBX-120)
            self.hw_subtype = iteration_config[rx_id + "_hw_subtype"]
            # "Hardware serial number, i.e. for USRP: mboard serial number
            self.seid = iteration_config[rx_id + "_seid"]
            # "HW RF maximum supported bandwidth
            self.max_RF_bandwidth = iteration_config[rx_id + "_max_RF_bandwidth"]

            # initialize rx parameters
            self.num_rx_samps = 0
            self.coerced_rx_rate = 0.0
            self.coerced_rx_freq = 0.0
            self.coerced_rx_gain = 0.0
            self.coerced_rx_bandwidth = 0.0
            self.coerced_rx_lo_source = 0.0
            # channel parameters of this RX
            # expected channel atteuntion, type = float"
            self.channel_attenuation = iteration_config[rx_id + "_channel_attenuation"]

    ## Get Hw type, subtype and HW ID of TX and RX stations
    # For USRP:
    # HW type = USRP type, mboard ID, i.e. USRP X310
    # HW subtype = USRP daughterboard type
    # HW seid = USRP serial number
    # This extra step is a workaround to solve two limitations in UHD
    # For TX and RX: the master clock rate cannot be changed after opening the session
    # We need to know mBoard ID to select the proper master clock rate in advance
    # For TX based on RFNoc graph: Getting USRP SN is supported in Multi-USRP but not on RFNoC graph
    def get_hardware_info(self, variations_map, enable_console_logging: bool):
        variations_product = variations_map.variations_product
        general_config = variations_map.general_config

        def get_usrp_mboard_info(num_usrps, RFmode, variations_product):
            for n in range(num_usrps):
                idx = n + 1
                args_list = variations_product[RFmode + str(idx) + "_args"]
                args = args_list[0]
                # open the session to USRP
                usrp = uhd.usrp.MultiUSRP(args)
                # get USRP daughterboard ID, UBX, CBX ...etc
                if RFmode == RFDataRecorderAPI.RFmode[0]:
                    usrp_info = usrp.get_usrp_tx_info()
                    usrp_bandwidth = usrp.get_tx_bandwidth()
                    usrp_daughterboard_id = usrp_info["tx_id"]
                else:
                    usrp_info = usrp.get_usrp_rx_info()
                    usrp_daughterboard_id = usrp_info["rx_id"]
                    usrp_bandwidth = usrp.get_rx_bandwidth()
                # get USRP type, i.e. X310
                usrp_mboard_id = usrp_info["mboard_id"]
                temp = usrp_daughterboard_id.split(" ")
                usrp_daughterboard_id_wo_ref = temp[0]
                # get USRP serial number
                usrp_serial_number = usrp_info["mboard_serial"]

                if enable_console_logging:
                    print(RFmode, " USRP number ", idx, " info:")
                    print(
                        "usrp_mboard_id:",
                        usrp_mboard_id,
                        ", usrp_serial_number:",
                        usrp_serial_number,
                        ", usrp_daughterboard_id:",
                        usrp_daughterboard_id_wo_ref,
                        ", usrp_RF_bandwidth:",
                        usrp_bandwidth,
                    )

                data_frame_i = pd.DataFrame(
                    {RFmode + str(idx) + "_hw_type": ["USRP " + usrp_mboard_id]}
                )
                variations_product = variations_product.merge(data_frame_i, how="cross")

                data_frame_i = pd.DataFrame(
                    {RFmode + str(idx) + "_hw_subtype": [usrp_daughterboard_id_wo_ref]}
                )
                variations_product = variations_product.merge(data_frame_i, how="cross")

                data_frame_i = pd.DataFrame({RFmode + str(idx) + "_seid": [usrp_serial_number]})
                variations_product = variations_product.merge(data_frame_i, how="cross")

                data_frame_i = pd.DataFrame(
                    {RFmode + str(idx) + "_max_RF_bandwidth": [usrp_bandwidth]}
                )
                variations_product = variations_product.merge(data_frame_i, how="cross")

            return variations_product

        # get hW info of TX Stations

        num_tx_usrps = int(general_config["num_tx_usrps"])
        if num_tx_usrps > 0:
            # if Tx station is USRP
            variations_product = get_usrp_mboard_info(
                num_tx_usrps, RFDataRecorderAPI.RFmode[0], variations_product
            )

        # get hW info of RX Stations
        num_rx_usrps = int(general_config["num_rx_usrps"])
        if num_rx_usrps > 0:
            # if Rx station is USRP
            variations_product = get_usrp_mboard_info(
                num_rx_usrps, RFDataRecorderAPI.RFmode[1], variations_product
            )

        if enable_console_logging:
            print("Updated variations cross product including Tx and RX stations HW info: ")
            print(variations_product)

        # Store variations product in its class
        variations_map.variations_product = variations_product

        return variations_map

    ## Read tdms waveform data config from rfws file
    def read_tdms_waveform_config(path, file, default_waveform_config_file):
        folder_path = (Path(__file__).parent / path).resolve()
        # The tdms waveform config file is saved with the same name of waveform but it has .rfws extenstion
        file_path = str(folder_path) + "/" + file + ".rfws"

        # reading the rfws file
        xmlDoc = ET.parse(file_path)
        root = xmlDoc.getroot()

        # XPath expressiion searching all elements recursively starting from root './/*'
        # that have an attribute 'name' with the value e.i. 'Bandwidth (Hz)'
        # returns a list, either iterate over the list or select list element zero [0] if you expect only one hit
        # more sophisticated expressions are possible
        waveform_config = RFDataRecorderAPI.initialize_waveform_config(default_waveform_config_file)

        # get standard
        factory = root.findall(".//*[@name='factory']")
        standard = factory[0].text
        waveform_config["standard"] = standard

        # Get parameters of NR standard
        if "NR" in standard:

            # get bandwidth
            bwElements = root.findall(".//*[@name='Bandwidth (Hz)']")
            bw = bwElements[0].text
            waveform_config["bandwidth"] = RFDataRecorderAPI.freq_string_to_float(bw)

            # get frequency range
            freqRanges = root.findall(".//*[@name='Frequency Range']")
            FR = freqRanges[0].text
            waveform_config["frequency_range"] = FR

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
                    waveform_config["test_model"] = "3GPP " + standard + "-" + dl_test_model

                    # get modulation type
                    mod = root.findall(".//*[@name='DL Test Model Modulation Type']")
                    # for PDSCH, select first catch, for PUSCH select second catch
                    mod = mod[0].text
                    waveform_config["modulation"] = mod

                    # get DL duplex
                    dl_duplex = root.findall(".//*[@name='DL Test Model Duplex Scheme']")
                    dl_duplex = dl_duplex[0].text
                    waveform_config["duplexing"] = dl_duplex

                elif dl_ch_config_mode == "User Defined":
                    # get DL test model
                    waveform_config["test_model"] = dl_ch_config_mode

                    # get modulation type
                    mod = root.findall(".//*[@name='Modulation Type']")
                    # for PDSCH, select first catch, for PUSCH select second catch
                    mod = mod[0].text
                    waveform_config["modulation"] = mod

                    # get DL duplex
                    waveform_config["duplexing"] = dl_ch_config_mode
            elif waveform_config["link_direction"] == "Uplink":
                # get DL test model, no test model for Uplink
                waveform_config["test_model"] = "User Defined"

                # get modulation type
                mod = root.findall(".//*[@name='Modulation Type']")
                # for PDSCH, select first catch, for PUSCH select second catch
                mod = mod[1].text
                waveform_config["modulation"] = mod

                # get DL duplex
                waveform_config["duplexing"] = "User Defined"
            else:
                raise Exception("ERROR: Unkown or not supported link direction")

            # get subcarrier spacing
            scs = root.findall(".//*[@name='Subcarrier Spacing (Hz)']")
            scs = scs[0].text
            waveform_config["subcarrier_spacing"] = scs

            # get CC index
            cc_index = root.findall(".//*[@name='CarrierCCIndex']")
            cc_index = cc_index[0].text
            waveform_config["carrier_CC_index"] = cc_index

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
            tx_data_complex, waveform_IQ_rate = RFDataRecorderAPI.read_tdms_waveform_data(
                path, file
            )
            waveform_config["rate"] = waveform_IQ_rate

        elif "LTE" in standard:

            def get_lte_parameter_config(key, str_idx):
                y = key.find("_" + str_idx)
                req_key = key[y + 3 :]
                return req_key

            # get bandwidth
            bwElements = root.findall(".//*[@name='Bandwidth']")
            bw_str = bwElements[0].text
            # the output likes this: "afGenLte_bw10MHz"
            bw = get_lte_parameter_config(bw_str, "bw")
            bw_wo_unit = bw[:-2]
            waveform_config["bandwidth"] = RFDataRecorderAPI.freq_string_to_float(bw_wo_unit)

            # get link direction
            link_directions = root.findall(".//*[@name='LinkDirection']")
            link_direction_str = link_directions[0].text
            link_direction = get_lte_parameter_config(link_direction_str, "ld")
            waveform_config["link_direction"] = link_direction

            # get number of frames
            waveform_config["n_frames"] = "1"

            # get test model
            test_models = root.findall(".//*[@name='TestModel']")
            test_model_str = test_models[0].text
            test_model = get_lte_parameter_config(test_model_str, "tm")
            waveform_config["test_model"] = "3GPP " + standard + "-" + test_model

            # get subcarrier spacing
            waveform_config["subcarrier_spacing"] = "15kHz"

            # multiplexing
            waveform_config["multiplexing"] = "OFDM"
            # multiple access
            waveform_config["multiple_access"] = ""

            # get rate
            tx_data_complex, waveform_IQ_rate = RFDataRecorderAPI.read_tdms_waveform_data(
                path, file
            )
            waveform_config["rate"] = waveform_IQ_rate

        return waveform_config

    ## Read waveform data config in matlab format for IEEE waveform generator
    def read_matlab_ieee_waveform_config(path, file, default_waveform_config_file):
        folder_path = (Path(__file__).parent / path / str(file)).resolve()
        file_path = str(folder_path) + "/cfg.csv"

        with open(file_path, "r") as file_p:
            csv_dicts = csv.DictReader(filter(lambda row: row[0] != "#", file_p), delimiter=";")
            # only one row of values is expected
            for row in csv_dicts:
                cfg_dict = row

        if cfg_dict["mods"] in RFDataRecorderAPI.modulation_schemes.keys():
            cfg_dict["mods"] = RFDataRecorderAPI.modulation_schemes[cfg_dict["mods"]]
        else:
            raise Exception("ERROR: Unsupported modulation scheme")

        # create harmonized dictionary
        waveform_config = RFDataRecorderAPI.initialize_waveform_config(default_waveform_config_file)
        waveform_config["standard"] = file
        waveform_config["multiplexing"] = "OFDM"
        waveform_config["bandwidth"] = float(cfg_dict["BW_str"]) * 1e6
        # get rate  -->  in wifi sampling rate = bandwidth
        waveform_config["rate"] = waveform_config["bandwidth"]
        waveform_config["MCS"] = cfg_dict["mcs"]
        waveform_config["code_rate"] = cfg_dict["crate"]
        waveform_config["modulation"] = cfg_dict["mods"]
        waveform_config["IEEE_MAC_frame_type"] = cfg_dict["format"]
        waveform_config["IEEE_PSDU_length_bytes"] = cfg_dict["PSDU_length"]

        return waveform_config

    def read_matlab_waveform_config(path, file, default_waveform_config_file):
        folder_path = (Path(__file__).parent / path).resolve()
        # The mat waveform config file is saved with the same name of waveform but in csv
        file_path = str(folder_path) + "/" + file + ".csv"
        with open(file_path, "r") as file_p:
            csvreader = csv.reader(filter(lambda row: row[0] != "#", file_p))
            cfg_dict = {}
            for row in csvreader:
                cfg_dict[row[0]] = row[1]
        # create harmonized dictionary
        waveform_config = RFDataRecorderAPI.initialize_waveform_config(default_waveform_config_file)
        waveform_config["standard"] = cfg_dict["standard"]
        waveform_config["bandwidth"] = RFDataRecorderAPI.freq_string_to_float(cfg_dict["bandwidth"])
        waveform_config["rate"] = RFDataRecorderAPI.freq_string_to_float(cfg_dict["rate"])
        waveform_config["n_frames"] = cfg_dict["n_frames"]

        return waveform_config

    # read waveform config
    def read_waveform_config(self, tx_data_recording_api_config, default_waveform_config_file):
        waveform_path = tx_data_recording_api_config.waveform_path
        waveform_file_name = tx_data_recording_api_config.waveform_file_name
        if tx_data_recording_api_config.waveform_format == "tdms":
            tx_data_recording_api_config.waveform_config = (
                RFDataRecorderAPI.read_tdms_waveform_config(
                    waveform_path,
                    waveform_file_name,
                    default_waveform_config_file,
                )
            )
        elif tx_data_recording_api_config.waveform_format == "matlab_ieee":
            tx_data_recording_api_config.waveform_config = (
                RFDataRecorderAPI.read_matlab_ieee_waveform_config(
                    waveform_path,
                    waveform_file_name,
                    default_waveform_config_file,
                )
            )
        elif tx_data_recording_api_config.waveform_format == "matlab":
            tx_data_recording_api_config.waveform_config = (
                RFDataRecorderAPI.read_matlab_waveform_config(
                    waveform_path,
                    waveform_file_name,
                    default_waveform_config_file,
                )
            )
        else:
            waveform_config = RFDataRecorderAPI.initialize_waveform_config(
                default_waveform_config_file
            )
            waveform_config["Standard"] = "unknown"
            tx_data_recording_api_config.waveform_config = waveform_config

        return tx_data_recording_api_config

    ## Read waveform data in TDMS format
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

    ## Update TX rate based on user selection:
    # "waveform_config": Set TX rate and bandwith based on waveform config
    # "user_defined": use the given value by the user in the config file: config_rf_data-recording_api
    def update_tx_rate(txs_data_recording_api_config):

        # Start for loop to update each TX config based on its rate config source
        for tx_idx, tx_data_recording_api_config in enumerate(txs_data_recording_api_config):
            if tx_data_recording_api_config.rate_source == "waveform_config":
                tx_data_recording_api_config.bandwidth = (
                    tx_data_recording_api_config.waveform_config["bandwidth"]
                )
                tx_data_recording_api_config.rate = tx_data_recording_api_config.waveform_config[
                    "rate"
                ]
            txs_data_recording_api_config[tx_idx] = tx_data_recording_api_config

        return txs_data_recording_api_config

    ## Update RX rate based on user selection:
    # "waveform_config": Set RX rate and bandwith based on waveform config
    #                    In case of multi Tx: Use the max bandwith and max rate of TX USRPs as a reference on RX
    # "user_defined": use the given value by the user in the config file: config_rf_data-recording_api
    def update_rx_rate(rxs_data_recording_api_config, txs_data_recording_api_config):

        # Initialize max rate and bandwidth
        max_tx_bandwidth = 0.0
        max_tx_rate = 0.0
        # Start for loop to update each RX based on its rate config source
        for rx_idx, rx_data_recording_api_config in enumerate(rxs_data_recording_api_config):
            if rx_data_recording_api_config.rate_source == "waveform_config":
                # find max rate and bandwidth of all TX USRPs
                # Do this check just for first RX USRP
                # The max values of TX usrps are valid for each Rx if it is configured to use "waveform_config"
                if rx_idx == 0:
                    for tx_idx, tx_data_recording_api_config in enumerate(
                        txs_data_recording_api_config
                    ):
                        if tx_data_recording_api_config.bandwidth > max_tx_bandwidth:
                            max_tx_bandwidth = tx_data_recording_api_config.bandwidth
                        if tx_data_recording_api_config.rate > max_tx_rate:
                            max_tx_rate = tx_data_recording_api_config.rate
                rx_data_recording_api_config.bandwidth = max_tx_bandwidth
                rx_data_recording_api_config.rate = max_tx_rate
            rxs_data_recording_api_config[rx_idx] = rx_data_recording_api_config

        return rxs_data_recording_api_config

    ## Update TX and RX rate based on user selection:
    # "waveform_config": Set TX or RX rate and bandwith based on waveform config
    #                    In case of multi Tx: Use the max bandwith and max rate of TX USRPs as a reference on RX
    # "user_defined": use the given value by the user in the config file: config_rf_data-recording_api
    def update_rate(self, txs_data_recording_api_config, rxs_data_recording_api_config):
        # First: Update TX Rate
        txs_data_recording_api_config = RFDataRecorderAPI.update_tx_rate(
            txs_data_recording_api_config
        )
        # Then: Update RX rate
        rxs_data_recording_api_config = RFDataRecorderAPI.update_rx_rate(
            rxs_data_recording_api_config, txs_data_recording_api_config
        )

        return txs_data_recording_api_config, rxs_data_recording_api_config

    ## Find proper master clock rate
    def calculate_master_clock_rate(requested_rate, usrp_mboard_id, args_in):
        def round_up_to_even(f):
            return math.ceil(f / 2.0) * 2

        # Derive master clock rate for X310 / X300 USRP
        if "X3" in usrp_mboard_id:
            # There are two master clock rates (MCR) supported on the X300 and X310: 200.0 MHz and 184.32 MHz.
            # The achievable sampling rates are by using an even decimation factor
            master_clock_rate_x310 = [200e6, 184.32e6]

            # Calculate the ratio between MCR and requested sampling rate
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

        # Derive master clock rate for other USRPs is not supported yet
        else:
            print("Warning: The code can derive the master clock rate for X310/X300 USRPs only.")
            print("         The default master clock rate will be used.")
            args_out = args_in

        return args_out

    # Calculate USRP master clockrate based on given rate
    def find_proper_master_clock_rate(
        self, txs_data_recording_api_config, rxs_data_recording_api_config
    ):
        # Find master clock rate for TX USRPs
        for tx_idx, tx_data_recording_api_config in enumerate(txs_data_recording_api_config):
            tx_data_recording_api_config.args = RFDataRecorderAPI.calculate_master_clock_rate(
                tx_data_recording_api_config.rate,
                tx_data_recording_api_config.hw_type,
                tx_data_recording_api_config.args,
            )
            txs_data_recording_api_config[tx_idx] = tx_data_recording_api_config

        # Find master clock rate for RX USRPs
        for rx_idx, rx_data_recording_api_config in enumerate(rxs_data_recording_api_config):
            rx_data_recording_api_config.args = RFDataRecorderAPI.calculate_master_clock_rate(
                rx_data_recording_api_config.rate,
                rx_data_recording_api_config.hw_type,
                rx_data_recording_api_config.args,
            )
            rxs_data_recording_api_config[rx_idx] = rx_data_recording_api_config

        return txs_data_recording_api_config, rxs_data_recording_api_config

    # print iteration config
    def print_iteration_config(
        self,
        iteration_config,
        general_config,
        txs_data_recording_api_config,
        rxs_data_recording_api_config,
    ):
        import warnings

        warnings.filterwarnings("ignore")
        for tx_idx, tx_data_recording_api_config in enumerate(txs_data_recording_api_config):
            iteration_config[
                RFDataRecorderAPI.RFmode[0] + str(tx_idx + 1) + "_rate"
            ] = tx_data_recording_api_config.rate
            iteration_config[
                RFDataRecorderAPI.RFmode[0] + str(tx_idx + 1) + "_bandwidth"
            ] = tx_data_recording_api_config.bandwidth

        for rx_idx, rx_data_recording_api_config in enumerate(rxs_data_recording_api_config):
            iteration_config[
                RFDataRecorderAPI.RFmode[1] + str(rx_idx + 1) + "_rate"
            ] = rx_data_recording_api_config.rate
            iteration_config[
                RFDataRecorderAPI.RFmode[1] + str(rx_idx + 1) + "_bandwidth"
            ] = rx_data_recording_api_config.bandwidth
        warnings.filterwarnings("default")
        print("Iteration config: ")
        print(iteration_config)
        print("General config: ")
        print(general_config)

    ## Use Ctrl-handler to stop TX in case of Tx Only
    def call_stop_tx_siganl():
        # Ctrl+C handler
        def signal_handler(sig, frame):
            print("Exiting . . .")
            sync_settings.stop_tx_signal_called = True

        # Wait until the Tx station is ready and then print how to stop tx
        while sync_settings.start_rx_data_acquisition_called == False:
            time.sleep(0.1)  # sleep for 100ms

        # ** Wait until user says to stop **
        # Setup SIGINT handler (Ctrl+C)
        signal.signal(signal.SIGINT, signal_handler)
        print("")
        print("Press Ctrl+C to stop RF streaming for this iteration ...")
        while sync_settings.stop_tx_signal_called == False:
            time.sleep(0.1)  # sleep for 100ms

    ## Start execution - TX emitters in parallel
    def start_execution_txs_in_parallel(
        self,
        txs_data_recording_api_config,
        rxs_data_recording_api_config,
        api_operation_mode,
        general_config,
        rx_data_nbytes_que,
    ):

        # initialize threads
        threads = []
        # start transmitters
        for idx, tx_data_recording_api_config in enumerate(txs_data_recording_api_config):
            process = threading.Thread(
                target=run_rf_replay_data_transmitter.rf_replay_data_transmitter,
                args=(
                    txs_data_recording_api_config[idx],
                    api_operation_mode,
                ),
            )
            process.start()
            threads.append(process)

        # start receivers
        # Trigger Rx:
        # ---------The data acquisition will start as soon as one Tx station is ready and started signal transmission
        # ---------The flag: "sync_settings.start_rx_data_acquisition_called" is used for that
        # Stop Tx:
        # ------ As soon as the Rx data is recorded, the txs will stop data tranmission
        # ------ The flag "sync_settings.stop_tx_signal_called" is used for that
        for idx, rx_data_recording_api_config in enumerate(rxs_data_recording_api_config):
            process = threading.Thread(
                target=run_rf_data_recorder.rf_data_recorder,
                args=(
                    rxs_data_recording_api_config[idx],
                    txs_data_recording_api_config,
                    general_config,
                    rx_data_nbytes_que,
                ),
            )
            process.start()
            threads.append(process)

        # For Tx-only mode: the stop tx signal is done manaully using Ctrl+C command
        if api_operation_mode == RFDataRecorderAPI.API_operation_modes[0]:
            # Ctrl+C handler
            RFDataRecorderAPI.call_stop_tx_siganl()

        # We now pause execution on the main thread by 'joining' all of our started threads.
        # This ensures that each has finished processing the urls.
        for process in threads:
            process.join()

        # settling time
        time.sleep(0.05)

    ## Start execution - TX emitters in sequential
    def start_execution_txs_in_sequential(
        self,
        txs_data_recording_api_config,
        rxs_data_recording_api_config,
        api_operation_mode,
        general_config,
        rx_data_nbytes_que,
        enable_console_logging,
    ):

        for idx, tx_data_recording_api_config in enumerate(txs_data_recording_api_config):
            ##  Initlize sync settings
            sync_settings.init()
            if enable_console_logging:
                print(
                    "Sync Status: Start Data Acquestion called = ",
                    sync_settings.start_rx_data_acquisition_called,
                    " Stop Tx Signal called = ",
                    sync_settings.stop_tx_signal_called,
                )
            # initialize threads
            threads = []
            # start transmitter
            process = threading.Thread(
                target=run_rf_replay_data_transmitter.rf_replay_data_transmitter,
                args=(
                    txs_data_recording_api_config[idx],
                    api_operation_mode,
                ),
            )
            process.start()
            threads.append(process)

            # start receivers
            # Trigger Rx:
            # ---------The data acquisition will start as soon as one Tx station is ready and started signal transmission
            # ---------The flag: "sync_settings.start_rx_data_acquisition_called" is used for that
            # Stop Tx:
            # ------ As soon as the Rx data is recorded, the txs will stop data tranmission
            # ------ The flag "sync_settings.stop_tx_signal_called" is used for that
            for idx, rx_data_recording_api_config in enumerate(rxs_data_recording_api_config):
                process = threading.Thread(
                    target=run_rf_data_recorder.rf_data_recorder,
                    args=(
                        rxs_data_recording_api_config[idx],
                        txs_data_recording_api_config,
                        general_config,
                        rx_data_nbytes_que,
                    ),
                )
                process.start()
                threads.append(process)

            # Tx-only mode
            if api_operation_mode == RFDataRecorderAPI.API_operation_modes[0]:
                # Ctrl+C handler
                RFDataRecorderAPI.call_stop_tx_siganl(api_operation_mode)

            # We now pause execution on the main thread by 'joining' all of our started threads.
            # This ensures that each has finished processing the urls.
            for process in threads:
                process.join()

            # settling time
            time.sleep(0.05)

    ## Execute Rxs only for RX only mode
    def start_rxs_execution(
        self,
        txs_data_recording_api_config,
        rxs_data_recording_api_config,
        general_config,
        rx_data_nbytes_que,
    ):

        threads = []
        # For Rx only, no trigger required from Tx to start data acquisition
        # Send a command to start RX data aquestions
        sync_settings.start_rx_data_acquisition_called = True

        for idx, rx_data_recording_api_config in enumerate(rxs_data_recording_api_config):
            process = threading.Thread(
                target=run_rf_data_recorder.rf_data_recorder,
                args=(
                    rxs_data_recording_api_config[idx],
                    txs_data_recording_api_config,
                    general_config,
                    rx_data_nbytes_que,
                ),
            )
            process.start()
            threads.append(process)

        # We now pause execution on the main thread by 'joining' all of our started threads.
        # This ensures that each has finished processing the urls.
        for process in threads:
            process.join()

        # settling time
        time.sleep(0.05)
