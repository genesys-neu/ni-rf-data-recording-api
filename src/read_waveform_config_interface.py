#
# Copyright 2022 National Instruments Corporation
#
# SPDX-License-Identifier: MIT
#
"""
Read Waveform Config Interface
"""
# Description:
#   The waveform configuration interface reads the configuration file and maps the parameter name of waveform creator to SigMF meta data
# 	    -   waveform (path, name, format)
#       -   wireless link parameter map
#
import os
import yaml
import numpy as np

# to read csv file of matlab waveform created using IEEE reference generator
import csv

# from timeit import default_timer as timer
from pathlib import Path

# check if file exists
from os.path import exists

# to read tdms properties from rfws file
# https://www.datacamp.com/community/tutorials/python-xml-elementtree
from re import X
import xml.etree.cElementTree as ET

# to search string between two strings
import re

# import related functions
import rf_data_recording_api_def
import read_waveform_data_interface
import data_format_conversion_lib

# Get 5G NR Waveform parameters from RFmx RFWS config
def get_nr_waveform_parameters_from_rfws_format(
    waveform_path, waveform_file_name, wireless_link_parameter_map
):
    # Note: The wireless_link_parameter_map is not used to get parameters from RFWS waveform config file
    # Due to the dependency between parameters; it requires hierarchical parameter extraction.

    ## Get file path
    folder_path = (Path(__file__).parent / waveform_path).resolve()
    # The tdms waveform config file is saved with the same name of waveform but it has .rfws extension
    file_path = os.path.join(folder_path, waveform_file_name + ".rfws")

    ## Load Waveform Config from rfws file
    xmlDoc = ET.parse(file_path)
    root = xmlDoc.getroot()
    # XPath expressiion searching all elements recursively starting from root './/*'
    # that have an attribute 'name' with the value e.i. 'Bandwidth (Hz)'
    # returns a list, either iterate over the list or select list element zero [0] if you expect only one hit
    # more sophisticated expressions are possible

    # Preallocate target dict for waveform config
    waveform_config = {}

    # get standard
    factory = root.findall(".//*[@name='factory']")
    standard = factory[0].text
    waveform_config["standard"] = standard

    # get frequency range
    freqRanges = root.findall(".//*[@name='Frequency Range']")
    FR = freqRanges[0].text
    waveform_config["frequency_range"] = FR

    # get bandwidth
    bwElements = root.findall(".//*[@name='Bandwidth (Hz)']")
    bw = bwElements[0].text
    waveform_config["bandwidth"] = data_format_conversion_lib.freq_string_to_float(bw)

    # get link direction
    link_directions = root.findall(".//*[@name='Link Direction']")
    link_direction = link_directions[0].text
    waveform_config["link_direction"] = link_direction

    # get number of frames
    n_frames = root.findall(".//*[@name='Number of Frames']")
    n_frames = n_frames[0].text
    waveform_config["n_frames"] = n_frames

    # get subcarrier spacing
    scs = root.findall(".//*[@name='Subcarrier Spacing (Hz)']")
    scs = scs[0].text
    waveform_config["subcarrier_spacing"] = data_format_conversion_lib.freq_string_to_float(scs)

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
            waveform_config["pdsch:modulation"] = mod

            # get frame structure - duplexing scheme
            dl_duplex = root.findall(".//*[@name='DL Test Model Duplex Scheme']")
            dl_duplex = dl_duplex[0].text
            waveform_config["frame_structure"] = dl_duplex

        elif dl_ch_config_mode == "User Defined":
            # get DL test model
            waveform_config["test_model"] = dl_ch_config_mode

            # get modulation type
            mod = root.findall(".//*[@name='Modulation Type']")
            # for PDSCH, select first catch, for PUSCH select second catch
            mod = mod[0].text
            waveform_config["pdsch:modulation"] = mod

            # get frame structure - duplexing scheme
            waveform_config["frame_structure"] = dl_ch_config_mode

    elif waveform_config["link_direction"] == "Uplink":
        # get DL test model, no test model for Uplink
        waveform_config["test_model"] = "User Defined"

        # get modulation type
        mod = root.findall(".//*[@name='Modulation Type']")
        # for PDSCH, select first catch, for PUSCH select second catch
        mod = mod[1].text
        waveform_config["pusch:modulation"] = mod

        # get frame structure - duplexing scheme
        waveform_config["frame_structure"] = "User Defined"
    else:
        raise Exception(
            "ERROR: Unkown or not supported link direction (Downlink or Uplink):",
            waveform_config["link_direction"],
        )

    # get rate
    tx_data_complex, waveform_IQ_rate = read_waveform_data_interface.read_waveform_data_tdms(
        waveform_path, waveform_file_name
    )
    waveform_config["sampling_rate"] = waveform_IQ_rate

    return waveform_config


# Get LTE Waveform parameters from RFmx RFWS config
def get_lte_waveform_parameters_from_rfws_format(
    waveform_path, waveform_file_name, wireless_link_parameter_map
):
    # Note: The wireless_link_parameter_map is not used to get parameters from RFWS waveform config file
    # Due to the dependency between parameters; it requires hierarchical parameter extraction.

    def get_lte_parameter_config(key, str_idx):
        y = key.find("_" + str_idx)
        req_key = key[y + 3 :]
        return req_key

    ## Get file path
    folder_path = (Path(__file__).parent / waveform_path).resolve()
    # The tdms waveform config file is saved with the same name of waveform but it has .rfws extenstion
    file_path = os.path.join(folder_path, waveform_file_name + ".rfws")

    ## Load Waveform Config from rfws file
    xmlDoc = ET.parse(file_path)
    root = xmlDoc.getroot()
    # XPath expressiion searching all elements recursively starting from root './/*'
    # that have an attribute 'name' with the value e.i. 'Bandwidth (Hz)'
    # returns a list, either iterate over the list or select list element zero [0] if you expect only one hit
    # more sophisticated expressions are possible

    # Preallocate target dict for waveform config
    waveform_config = {}

    ## get standard
    factory = root.findall(".//*[@name='factory']")
    standard = factory[0].text
    waveform_config["standard"] = standard

    # get frame structure
    import re

    result = re.search(" (.*) ", standard)
    waveform_config["frame_structure"] = result.group(1)

    # get bandwidth
    bwElements = root.findall(".//*[@name='Bandwidth']")
    bw_str = bwElements[0].text
    # the output likes this: "afGenLte_bw10MHz"
    bw = get_lte_parameter_config(bw_str, "bw")
    bw_wo_unit = bw[:-2]
    waveform_config["bandwidth"] = data_format_conversion_lib.freq_string_to_float(bw_wo_unit)

    # get link direction
    link_directions = root.findall(".//*[@name='LinkDirection']")
    link_direction_str = link_directions[0].text  #
    link_direction = get_lte_parameter_config(link_direction_str, "ld")
    waveform_config["link_direction"] = link_direction

    # get test model
    test_models = root.findall(".//*[@name='TestModel']")
    test_model_str = test_models[0].text
    test_model = get_lte_parameter_config(test_model_str, "tm")
    waveform_config["test_model"] = "3GPP " + standard + "-" + test_model

    if waveform_config["link_direction"] == "Downlink":
        # get modulation type
        mod = root.findall(".//*[@name='PDSCHCodeWord1ModulationType']")
        # Select the first hit, since every subframe has own modulation config
        mod = mod[0].text
        waveform_config["pdsch:modulation"] = get_lte_parameter_config(mod, "mt")

    elif waveform_config["link_direction"] == "Uplink":
        # get modulation type
        mod = root.findall(".//*[@name='User Defined Modulation Type']")
        # Select the first hit, since every subframe has own modulation config
        mod = mod[0].text
        waveform_config["pusch:modulation"] = get_lte_parameter_config(mod, "mt")
    else:
        raise Exception(
            "ERROR: Unkown or not supported link direction (Downlink or Uplink):",
            waveform_config["link_direction"],
        )

    # get subcarrier spacing
    waveform_config["subcarrier_spacing"] = 15000.0

    # get rate
    tx_data_complex, waveform_IQ_rate = read_waveform_data_interface.read_waveform_data_tdms(
        waveform_path, waveform_file_name
    )
    waveform_config["sampling_rate"] = waveform_IQ_rate

    return waveform_config


## Read tdms waveform data config from rfws file
def read_tdms_waveform_config(waveform_path, waveform_file_name, wireless_link_parameter_map):
    ## Get file path
    waveform_folder_path = (Path(__file__).parent / waveform_path).resolve()
    # The tdms waveform config file is saved with the same name of waveform but it has .rfws extenstion
    waveform_file_path = os.path.join(waveform_folder_path, waveform_file_name + ".rfws")
    # check if file exists
    file_exists = exists(waveform_file_path)
    if file_exists:
        ## Load Waveform Config from rfws file
        xmlDoc = ET.parse(waveform_file_path)
        root = xmlDoc.getroot()
        # Get standard
        factory = root.findall(".//*[@name='factory']")
        standard = factory[0].text

        # XPath expressiion searching all elements recursively starting from root './/*'
        # that have an attribute 'name' with the value e.i. 'Bandwidth (Hz)'
        # returns a list, either iterate over the list or select list element zero [0] if you expect only one hit
        # more sophisticated expressions are possible
    else:
        raise Exception("ERROR: Waveform Config file is not exist", waveform_file_path)

    # Get parameters based on standard
    if "NR" in standard:
        waveform_config = get_nr_waveform_parameters_from_rfws_format(
            waveform_path, waveform_file_name, wireless_link_parameter_map
        )
    elif "LTE" in standard:
        waveform_config = get_lte_waveform_parameters_from_rfws_format(
            waveform_path, waveform_file_name, wireless_link_parameter_map
        )
    else:
        raise Exception("ERROR: Unkown or not supported standard", standard)

    return waveform_config


def read_matlab_waveform_config(
    waveform_path, waveform_file_name, format, wireless_link_parameter_map_file
):
    """
    Read waveform configuration file and map metadata to dictionary conforming the API and SigMF format.
    The wireless link parameter map (YAML file) has the dictionary of used parameters and specify the mapping pairs.
    """
    # Read wavefrom configuration file in YAML format
    folder_path = (Path(__file__).parent / waveform_path).resolve()
    # Read waveform config in YAML format
    if format == "matlab":
        # The MATLAB waveform config file is saved with the same name of waveform but in yaml
        path_to_file = os.path.join(folder_path, waveform_file_name + ".yaml")

        # check if file exists
        file_exists = exists(path_to_file)
        if file_exists:
            with open(path_to_file, "r") as file:
                waveform_config_src = yaml.load(file, Loader=yaml.Loader)
        else:
            raise Exception("ERROR: Waveform Config file is not exist", path_to_file)
    # Read waveform config in CSV for waveforms created using IEEE generator in MATLAB
    elif format == "matlab_ieee":
        path_to_file = os.path.join(folder_path, waveform_file_name + "/cfg.csv")

        # check if file exists
        file_exists = exists(path_to_file)
        if file_exists:
            with open(path_to_file, "r") as file:
                waveform_config_src_temp = csv.DictReader(
                    filter(lambda row: row[0] != "#", file), delimiter=";"
                )
                # only one row of values is expected
                for row in waveform_config_src_temp:
                    waveform_config_src = row
        else:
            raise Exception("ERROR: Waveform Config file is not exist", path_to_file)

        # since in this matlab waveforms, the ieee generator does not write the standard key to config file, do it manaully
        waveform_config_src["standard"] = "802.11_ieee_gen_matlab"
        # map modulation order from index to string
        if (
            waveform_config_src["mods"]
            in rf_data_recording_api_def.RFDataRecorderAPI.modulation_schemes.keys()
        ):
            waveform_config_src[
                "mods"
            ] = rf_data_recording_api_def.RFDataRecorderAPI.modulation_schemes[
                waveform_config_src["mods"]
            ]
        else:
            raise Exception("ERROR: Unsupported modulation scheme", waveform_config_src["mods"])
    else:
        raise Exception("ERROR: Unsupported waveform format")

    # read standard:waveform config file in YAML format should have the standard key word
    standard = waveform_config_src["standard"]

    # read waveform parameter map from yaml file
    with open(
        os.path.join(os.path.dirname(__file__), wireless_link_parameter_map_file), "r"
    ) as file:
        wireless_link_parameter_map_dic = yaml.load(file, Loader=yaml.Loader)

    waveform_parameter_map_dic = wireless_link_parameter_map_dic["transmitter"][standard]

    # preallocate target dict
    waveform_config = {}

    for parameter_pair in waveform_parameter_map_dic:
        # only continue with mapping from file if direct equivalent exists
        if parameter_pair[standard + "_parameter_name"]:
            # extract value from waveform config file
            if parameter_pair[standard + "_parameter_name"] in waveform_config_src:
                value = waveform_config_src[parameter_pair[standard + "_parameter_name"]]
                if isinstance(value, str):
                    if (
                        parameter_pair["sigmf_parameter_name"] == "bandwidth"
                        or parameter_pair["sigmf_parameter_name"] == "sampling_rate"
                    ):
                        value = data_format_conversion_lib.freq_string_to_float(value)
                # write to target dictionary for SigMF
                waveform_config[parameter_pair["sigmf_parameter_name"]] = value
        else:  # fill_non_explicit_fields
            waveform_config[parameter_pair["sigmf_parameter_name"]] = "none"

    # check for non-JSON-serializable data types
    for key, value in waveform_config.items():
        if isinstance(value, np.integer):
            waveform_config[key] = int(value)
    return waveform_config


# read tx waveform config
def read_tx_waveform_config(tx_data_recording_api_config, wireless_link_parameter_map):
    # get waveform selection parameters
    waveform_path = tx_data_recording_api_config.waveform_path
    waveform_file_name = tx_data_recording_api_config.waveform_file_name
    waveform_format = tx_data_recording_api_config.waveform_format

    if waveform_format == "tdms":
        tx_data_recording_api_config.waveform_config = read_tdms_waveform_config(
            waveform_path,
            waveform_file_name,
            wireless_link_parameter_map,
        )
    elif waveform_format == "matlab" or waveform_format == "matlab_ieee":

        tx_data_recording_api_config.waveform_config = read_matlab_waveform_config(
            waveform_path,
            waveform_file_name,
            waveform_format,
            wireless_link_parameter_map,
        )
    else:
        waveform_config = {}
        waveform_config["Standard"] = "unknown"
        tx_data_recording_api_config.waveform_config = waveform_config

    return tx_data_recording_api_config


if __name__ == "__main__":

    # local class for testing
    class TxRFDataRecorderConfig:
        """Tx RFDataRecorder Config class"""

        def __init__(self):
            # ============= TX Config parameters =============
            # self.waveform_file_name = "NR_FR1_UL_All_SISO_BW-20MHz_CC-1_SCS-30kHz_Mod-64QAM_OFDM_enabled_PTRS"# NR_FR1_DL_FDD_SISO_BW-20MHz_CC-1_SCS-30kHz_Mod-64QAM_OFDM_TM3.1"
            self.waveform_file_name = (
                "LTE_TDD_UL_RMC_A2321_4_2_10MHz_6_7"  # LTE_FDD_DL_5MHz_CC-1_E-UTRA_E-TM3.1"
            )
            # self.waveform_file_name = "RadarWaveform_BW_1428k"
            # self.waveform_file_name = "IEEE_tx11ac_legacy_20MHz_80MSps_MCS7_27bytes_1frame"
            # "path to TDMS/mat/... file, type = str ",
            self.waveform_path = "waveform-files/tdms/"
            # "possible values: tdms, matlab_ieee, type = str ",
            self.waveform_format = "tdms"
            # Define dictionary for tx wavform config
            waveform_config = {}
            self.waveform_config = waveform_config

    wireless_link_parameter_map = "wireless_link_parameter_map.yaml"
    tx_data_recording_api_config = TxRFDataRecorderConfig()

    tx_data_recording_api_config = read_tx_waveform_config(
        tx_data_recording_api_config, wireless_link_parameter_map
    )
    waveform_config = tx_data_recording_api_config.waveform_config
    print(waveform_config)
    # attrs = vars(waveform_config)
    # print(', '.join("%s: %s" % item for item in attrs.items()))
