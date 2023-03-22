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

# import related functions
from lib import rf_data_recording_api_def
from lib import read_waveform_data_interface
from lib import data_format_conversion_lib

# Get 5G NR Waveform parameters from RFmx RFWS config
def get_nr_waveform_parameters_from_rfws_format(waveform_path, waveform_file_name):
    # Note: The wireless_link_parameter_map is not used to get parameters from RFWS waveform config file
    # Due to the dependency between parameters; it requires hierarchical parameter extraction.

    # Preallocate target dict for waveform config
    waveform_config_src = {}

    # waveform_config_src["generator"] ={"generator_abbr": "abbreviation",
    #                                   "generator_description":"description"}
    # generator_abbr: used to create parameter names in wireless_link_parameter_map
    # ............. if standard = nr, WaveformGenerator: ni_rfmx_rfws, then the parameter name: nr_ni_rfmx_rfws_parmater
    # generator_description: generator description to occur in meta-data
    #
    waveform_config_src["generator"] = {
        "generator_abbr": "ni_rfmx_rfws",
        "generator_description": "NI RFmx Waveform Creator: https://www.ni.com/en-ca/shop/wireless-design-test/application-software-for-wireless-design-test-category/what-is-rfmx.html",
    }

    # The tdms waveform config file is saved with the same name of waveform but it has .rfws extension
    waveform_file_path = os.path.join(waveform_path, waveform_file_name + ".rfws")

    ## Load Waveform Config from rfws file
    xmlDoc = ET.parse(waveform_file_path)
    root = xmlDoc.getroot()
    # XPath expressiion searching all elements recursively starting from root './/*'
    # that have an attribute 'name' with the value e.i. 'Bandwidth (Hz)'
    # returns a list, either iterate over the list or select list element zero [0] if you expect only one hit
    # more sophisticated expressions are possible

    # get standard
    factory = root.findall(".//*[@name='factory']")
    standard = factory[0].text
    # waveform_config_src["factory"] = "standard"
    waveform_config_src["standard"] = "5gnr"

    # get frequency range
    freqRanges = root.findall(".//*[@name='Frequency Range']")
    FR = freqRanges[0].text
    waveform_config_src["Frequency Range"] = FR

    # get bandwidth
    bwElements = root.findall(".//*[@name='Bandwidth (Hz)']")
    bw = bwElements[0].text
    waveform_config_src[
        "Bandwidth (Hz)"
    ] = data_format_conversion_lib.si_unit_string_converstion_to_float(bw)

    # get link direction
    link_directions = root.findall(".//*[@name='Link Direction']")
    link_direction = link_directions[0].text
    waveform_config_src["Link Direction"] = link_direction

    # get cell id
    cell_id = root.findall(".//*[@name='Cell ID']")
    cell_id_str = cell_id[0].text  #
    waveform_config_src["Cell ID"] = cell_id_str

    # get number of frames
    n_frames = root.findall(".//*[@name='Number of Frames']")
    n_frames = n_frames[0].text
    waveform_config_src["Number of Frames"] = n_frames

    # get subcarrier spacing
    scs = root.findall(".//*[@name='Subcarrier Spacing (Hz)']")
    scs = scs[0].text
    waveform_config_src[
        "Subcarrier Spacing (Hz)"
    ] = data_format_conversion_lib.si_unit_string_converstion_to_float(scs)

    # get Cyclic prefix mode
    cp_mode = root.findall(".//*[@name='Cyclic Prefix Mode']")
    cp_mode_str = cp_mode[0].text  #
    waveform_config_src["Cyclic Prefix Mode"] = cp_mode_str

    # get CC index
    # cc_index = root.findall(".//*[@name='CarrierCCIndex']")
    # cc_index = cc_index[0].text
    # waveform_config_src["carrier_CC_index"] = cc_index

    # get ssb info
    ssb_config_set = root.findall(".//*[@name='Configuration Set']")
    ssb_config_set = ssb_config_set[0].text
    waveform_config_src["Configuration Set"] = ssb_config_set

    # get ssb info
    ssb_scs = root.findall(".//*[@name='Subcarrier Spacing Common']")
    ssb_scs_str = ssb_scs[0].text
    waveform_config_src[
        "Subcarrier Spacing Common"
    ] = data_format_conversion_lib.si_unit_string_converstion_to_float(ssb_scs_str)

    # get ssb periodicity
    ssb_periodicity = root.findall(".//*[@name='Periodicity']")
    ssb_periodicity = ssb_periodicity[0].text
    waveform_config_src[
        "Periodicity"
    ] = data_format_conversion_lib.si_unit_string_converstion_to_float(ssb_periodicity)

    if waveform_config_src["Link Direction"] == "Downlink":
        # check if test model is enabled
        dl_ch_config_modes = root.findall(".//*[@name='DL Ch Configuration Mode']")
        dl_ch_config_mode = dl_ch_config_modes[0].text
        if dl_ch_config_mode == "Test Model":
            # get DL test model
            dl_test_models = root.findall(".//*[@name='DL Test Model']")
            dl_test_model = dl_test_models[0].text
            waveform_config_src["Test Model"] = dl_test_model

            # get modulation type
            mod = root.findall(".//*[@name='DL Test Model Modulation Type']")
            # for PDSCH, select first catch, for PUSCH select second catch
            mod = mod[0].text
            waveform_config_src["DL Modulation Type"] = mod

            # get frame structure - duplexing scheme
            dl_duplex = root.findall(".//*[@name='DL Test Model Duplex Scheme']")
            dl_duplex = dl_duplex[0].text
            waveform_config_src["Duplex Scheme"] = dl_duplex

        elif dl_ch_config_mode == "User Defined":
            # get DL test model
            waveform_config_src["Test Model"] = dl_ch_config_mode

            # get modulation type
            mod = root.findall(".//*[@name='Modulation Type']")
            # for PDSCH, select first catch, for PUSCH select second catch
            mod = mod[0].text
            waveform_config_src["DL Modulation Type"] = mod

            # get frame structure - duplexing scheme
            waveform_config_src["Duplex Scheme"] = dl_ch_config_mode

    elif waveform_config_src["Link Direction"] == "Uplink":
        # get DL test model, no test model for Uplink
        waveform_config_src["Test Model"] = "user_defined"

        # get modulation type
        mod = root.findall(".//*[@name='Modulation Type']")
        # for PDSCH, select first catch, for PUSCH select second catch
        mod = mod[1].text
        waveform_config_src["UL Modulation Type"] = mod

        # get frame structure - duplexing scheme
        waveform_config_src["Duplex Scheme"] = "user_defined"
    else:
        raise Exception(
            "ERROR: Unkown or not supported link direction (Downlink or Uplink):",
            waveform_config_src["link_direction"],
        )

    # get rate
    tx_data_complex, waveform_IQ_rate = read_waveform_data_interface.read_waveform_data_tdms(
        waveform_path, waveform_file_name
    )
    waveform_config_src["sample_rate_hz"] = waveform_IQ_rate

    return waveform_config_src


# Get LTE Waveform parameters from RFmx RFWS config
def get_lte_waveform_parameters_from_rfws_format(waveform_path, waveform_file_name):
    # Note: The wireless_link_parameter_map is not used to get parameters from RFWS waveform config file
    # Due to the dependency between parameters; it requires hierarchical parameter extraction.

    # Preallocate target dict for waveform config
    waveform_config_src = {}

    # waveform_config_src["generator"] ={"generator_abbr": "abbreviation",
    #                                   "generator_description":"description"}
    # generator_abbr: used to create parameter names in wireless_link_parameter_map
    # ............. if standard = nr, WaveformGenerator: ni_rfmx_rfws, then the parameter name: nr_ni_rfmx_rfws_parmater
    # generator_description: generator description to occur in meta-data
    #
    waveform_config_src["generator"] = {
        "generator_abbr": "ni_rfmx_rfws",
        "generator_description": "NI RFmx Waveform Creator: https://www.ni.com/en-ca/shop/wireless-design-test/application-software-for-wireless-design-test-category/what-is-rfmx.html",
    }

    def get_lte_parameter_config(key, str_idx):
        y = key.find("_" + str_idx)
        req_key = key[y + 3 :]
        return req_key

    # The tdms waveform config file is saved with the same name of waveform but it has .rfws extension
    waveform_file_path = os.path.join(waveform_path, waveform_file_name + ".rfws")

    ## Load Waveform Config from rfws file
    xmlDoc = ET.parse(waveform_file_path)
    root = xmlDoc.getroot()
    # XPath expressiion searching all elements recursively starting from root './/*'
    # that have an attribute 'name' with the value e.i. 'Bandwidth (Hz)'
    # returns a list, either iterate over the list or select list element zero [0] if you expect only one hit
    # more sophisticated expressions are possible

    ## get standard
    factory = root.findall(".//*[@name='factory']")
    standard = factory[0].text
    # waveform_config_src["factory"] = "standard"
    waveform_config_src["standard"] = "lte"

    # get frame structure
    import re

    result = re.search(" (.*) ", standard)
    waveform_config_src["factory"] = result.group(1)

    # get bandwidth
    bwElements = root.findall(".//*[@name='Bandwidth']")
    bw_str = bwElements[0].text
    # the output likes this: "afGenLte_bw10MHz"
    bw = get_lte_parameter_config(bw_str, "bw")
    bw_wo_unit = bw[:-2]
    waveform_config_src[
        "Bandwidth"
    ] = data_format_conversion_lib.si_unit_string_converstion_to_float(bw_wo_unit)

    # get link direction
    link_directions = root.findall(".//*[@name='LinkDirection']")
    link_direction_str = link_directions[0].text  #
    link_direction = get_lte_parameter_config(link_direction_str, "ld")
    waveform_config_src["LinkDirection"] = link_direction

    # get cell id
    cell_id = root.findall(".//*[@name='CellID']")
    cell_id_str = cell_id[0].text  #
    waveform_config_src["CellID"] = cell_id_str

    # get Cyclic prefix mode
    cp_mode = root.findall(".//*[@name='CyclicPrefixType']")
    cp_mode_str = cp_mode[0].text  #
    waveform_config_src["CyclicPrefixType"] = cp_mode_str

    # get test model
    test_models = root.findall(".//*[@name='TestModel']")
    test_model_str = test_models[0].text
    test_model = get_lte_parameter_config(test_model_str, "tm")
    waveform_config_src["TestModel"] = test_model

    if waveform_config_src["LinkDirection"] == "Downlink":
        # get modulation type
        mod = root.findall(".//*[@name='PDSCHCodeWord1ModulationType']")
        # Select the first hit, since every subframe has own modulation config
        mod = mod[0].text
        waveform_config_src["PDSCHCodeWord1ModulationType"] = get_lte_parameter_config(mod, "mt")

    elif waveform_config_src["LinkDirection"] == "Uplink":
        # get modulation type
        mod = root.findall(".//*[@name='User Defined Modulation Type']")
        # Select the first hit, since every subframe has own modulation config
        mod = mod[0].text
        waveform_config_src["User Defined Modulation Type"] = get_lte_parameter_config(mod, "mt")
    else:
        raise Exception(
            "ERROR: Unkown or not supported link direction (Downlink or Uplink):",
            waveform_config_src["LinkDirection"],
        )

    # get subcarrier spacing
    waveform_config_src["subcarrier_spacing"] = 15000.0

    # get rate
    tx_data_complex, waveform_IQ_rate = read_waveform_data_interface.read_waveform_data_tdms(
        waveform_path, waveform_file_name
    )
    waveform_config_src["sample_rate"] = waveform_IQ_rate

    return waveform_config_src


## Read tdms waveform data config from rfws file
def read_tdms_waveform_config(waveform_path, waveform_file_name):

    # The tdms waveform config file is saved with the same name of waveform but it has .rfws extension
    waveform_file_path = os.path.join(waveform_path, waveform_file_name + ".rfws")

    # check if file exists
    if exists(waveform_file_path):
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
        waveform_config_src = get_nr_waveform_parameters_from_rfws_format(
            waveform_path, waveform_file_name
        )
    elif "LTE" in standard:
        waveform_config_src = get_lte_waveform_parameters_from_rfws_format(
            waveform_path, waveform_file_name
        )
    else:
        raise Exception("ERROR: Unkown or not supported standard", standard)

    return waveform_config_src


def read_matlab_waveform_config(waveform_path, waveform_file_name, format):
    """
    Read waveform configuration file and map metadata to dictionary conforming the API and SigMF format.
    The wireless link parameter map (YAML file) has the dictionary of used parameters and specify the mapping pairs.
    """
    # Read wavefrom configuration file in YAML format
    if format == "matlab":
        # The MATLAB waveform config file is saved with the same name of waveform but in yaml
        path_to_file = os.path.join(waveform_path, waveform_file_name + ".yaml")

        # check if file exists
        file_exists = exists(path_to_file)
        if file_exists:
            with open(path_to_file, "r") as file:
                waveform_config_src = yaml.load(file, Loader=yaml.Loader)
        else:
            raise Exception("ERROR: Waveform Config file is not exist", path_to_file)

    # Read waveform config in CSV for waveforms created using 802.11 IEEE generator in MATLAB
    elif format == "matlab_ieee":
        path_to_file = os.path.join(waveform_path, waveform_file_name + "/cfg.csv")

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

        # Parameters pre-processing
        # change BW to MHz
        value = data_format_conversion_lib.si_unit_string_converstion_to_float(
            waveform_config_src["BW_str"]
        )
        waveform_config_src["BW_str"] = value * 1e6
        # change code rate to decimal, i.e. 3/7
        waveform_config_src["crate"] = eval(waveform_config_src["crate"])

        # since in this matlab waveforms, the ieee generator does not write the standard key to config file, do it manaully
        waveform_config_src["standard"] = "802.11"
        waveform_config_src["generator"] = "ieee_gen_matlab"

    else:
        raise Exception("ERROR: Unsupported waveform format")

    return waveform_config_src


def map_metadata_to_sigmf_format(waveform_config_src, wireless_link_parameter_map_file):
    """
    Maps metadata from Waveform creator to API and SigMF format.
    The used parameters and the mapping pairs are specified in a separate YAML file
    that must be provided as well.
    """
    # read waveform parameter map from yaml file
    dir_path = os.path.dirname(__file__)
    src_path = os.path.split(dir_path)[0]
    with open(os.path.join(src_path, "config", wireless_link_parameter_map_file), "r") as file:
        wireless_link_parameter_map_dic = yaml.load(file, Loader=yaml.Loader)

    # check if standard key is given
    if waveform_config_src.get("standard") is None:
        raise Exception(f"standard should be given via config file or added manually!")

    # check if waveform generator key is given
    if waveform_config_src.get("generator") is None:
        print("Error: waveform generator is used to derive the paramter name")
        raise Exception(f"waveform generator should be given via config file or added manually!")

    if waveform_config_src["standard"] == "802.11":
        waveform_parameter_map_dic = wireless_link_parameter_map_dic["transmitter"]["wifi"]
    else:
        waveform_parameter_map_dic = wireless_link_parameter_map_dic["transmitter"][
            waveform_config_src["standard"]
        ]
    # Get waveform generator info
    # It can be provided as
    # option1: waveform_parameter_map_dic["generator"] = "name" such as "ieee_gen_matlab"
    # option2: waveform_config_src["generator"] ={"generator_abbr": "abbreviation",
    #                                   "generator_description":"description"}
    # generator_abbr: used to create parameter names in wireless_link_parameter_map
    # ............. if standard = nr, WaveformGenerator: ni_rfmx_rfws, then the parameter name: nr_ni_rfmx_rfws_parmater
    # generator_description: generator description to occur in meta-data
    #
    if isinstance(waveform_config_src["generator"], dict):
        generator_abbr = data_source = waveform_config_src["generator"]["generator_abbr"]
        # keep generator_description and remove generator_abbr
        waveform_config_src["generator"] = waveform_config_src["generator"]["generator_description"]
    else:
        generator_abbr = data_source = waveform_config_src["generator"]
    # create common parameters key: StandardName +_ + WaveformGenerator
    data_source = waveform_config_src["standard"] + "_" + generator_abbr

    # pre-allocate target dict
    waveform_config = {}
    waveform_config ["standard"] = waveform_config_src["standard"]

    for parameter_pair in waveform_parameter_map_dic:
        # check if key for chosen simulator even exists
        if data_source + "_parameter" in parameter_pair.keys():
            # only continue with mapping from file if direct equivalent exists
            if parameter_pair[data_source + "_parameter"]["name"]:
                # It is not necessary to get all parameters from wireless_link_parameter_map.yaml in waveform_config_src
                # since some parameters related to DL or UL only
                if parameter_pair[data_source + "_parameter"]["name"] in waveform_config_src.keys():
                    # extract value from waveform config source
                    value = waveform_config_src[parameter_pair[data_source + "_parameter"]["name"]]
                    # additional mapping if parameter values should come from a discrete set of values
                    if "value_map" in parameter_pair[data_source + "_parameter"].keys():
                        value = parameter_pair[data_source + "_parameter"]["value_map"][value]
                    # write to target dictionary for SigMF
                    waveform_config[parameter_pair["sigmf_parameter_name"]] = value
            else:
                raise Exception(f"Incomplete specification in field '{data_source}_parameter'!")
        # else:  # fill_non_explicit_fields
        #     waveform_config[parameter_pair["sigmf_parameter_name"]] = "none"

    # check for non-JSON-serializable data types
    def isfloat(NumberString):
        try:
            float(NumberString)
            return True
        except ValueError:
            return False

    for key, value in waveform_config.items():
        if isinstance(value, np.integer):
            waveform_config[key] = int(value)
        elif isinstance(value, (np.float16, np.float32, np.float64)):
            waveform_config[key] = np.format_float_positional(value, trim="-")
        elif isinstance(value, int):
            waveform_config[key] = int(value)
        elif isinstance(value, float):
            # store value in decimal and not in scientific notation
            waveform_config[key] = float(value)
        elif isinstance(value, str) and key != "standard":
            # convert string to lower case
            waveform_config[key] = value.lower()
            if isfloat(value):
                if value.isdigit():
                    waveform_config[key] = int(float(value))
                elif value.replace(".", "", 1).isdigit() and value.count(".") < 2:
                    waveform_config[key] = float(value)

    return waveform_config


# read tx waveform config
def read_tx_waveform_config(tx_data_recording_api_config, wireless_link_parameter_map):

    # get waveform selection parameters
    waveform_path = tx_data_recording_api_config.waveform_path
    waveform_file_name = tx_data_recording_api_config.waveform_file_name
    waveform_format = tx_data_recording_api_config.waveform_format

    if waveform_format in ["tdms", "matlab", "matlab_ieee"]:
        if waveform_format == "tdms":
            waveform_config_src = read_tdms_waveform_config(
                waveform_path,
                waveform_file_name,
            )
        elif waveform_format in ["matlab", "matlab_ieee"]:

            waveform_config_src = read_matlab_waveform_config(
                waveform_path,
                waveform_file_name,
                waveform_format,
            )
        tx_data_recording_api_config.waveform_config = map_metadata_to_sigmf_format(
            waveform_config_src, wireless_link_parameter_map
        )
    else:
        waveform_config = {}
        waveform_config["standard"] = "unknown"
        tx_data_recording_api_config.waveform_config = waveform_config

    return tx_data_recording_api_config
