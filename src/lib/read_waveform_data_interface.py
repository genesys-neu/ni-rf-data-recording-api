#
# Copyright 2022 National Instruments Corporation
#
# SPDX-License-Identifier: MIT
#
"""
Read Waveform Data in TDMS/MATLAB format
"""
# Description:
#   The waveform data interface reads the waveform IQ data in TDMS / MATLAB format
# 	    - waveform (path, name, format)
#       - wireless link parameter map
#
import os
from pathlib import Path

# to read tdms file
from nptdms import TdmsFile

# to read MATLAB data
import scipy.io

# check if file exists
from os.path import exists

# plot waveform
import matplotlib.pyplot as plt

# ************************************************************************
#    * Read Waveforms functions
# ***********************************************************************/

## Read waveform data in TDMS format
def read_waveform_data_tdms(waveform_path, waveform_file_name):

    # The tdms waveform config file is saved with the same name of waveform but it has .rfws extenstion
    path_to_file = os.path.join(waveform_path, waveform_file_name + ".tdms")
    # check if file exists
    file_exists = exists(path_to_file)
    if file_exists:
        tdms_file = TdmsFile.read(path_to_file)

        # get all channels
        group = tdms_file["waveforms"]
        # get channel dat
        channel = ""
        if "Channel 0" in group:
            channel = group["Channel 0"]
        elif "segment0/channel0" in group:
            channel = group["segment0/channel0"]
        if not channel:
            raise Exception("ERROR: Unknown channel name of a given TDMS Waveform")

        waveform_IQ_rate = channel.properties["NI_RF_IQRate"]

        tx_data_float = channel[:]
        tx_data_complex = tx_data_float[::2] + 1j * tx_data_float[1::2]
    else:
        raise Exception("ERROR: Waveform Config file is not exist", path_to_file)

    return tx_data_complex, waveform_IQ_rate


## Read waveform data in MATLAB format for IEEE waveform generator
def read_waveform_data_matlab_ieee(waveform_path, waveform_file_name):

    waveform_file_path = os.path.join(waveform_path, waveform_file_name)
    mat_data = scipy.io.loadmat(str(waveform_file_path) + "/sbb_str.mat")
    # get data
    data = mat_data["sbb_str"]
    tx_data_complex = data[0][0][0]

    return tx_data_complex


## Read waveform data in MATLAB format - arbitrary mode
def read_waveform_data_matlab(waveform_path, waveform_file_name):

    waveform_file_path = os.path.join(waveform_path, waveform_file_name)
    mat_data = scipy.io.loadmat(str(waveform_file_path) + ".mat")
    # get data
    data = mat_data["waveform"]
    tx_data_complex = data.flatten()

    return tx_data_complex
