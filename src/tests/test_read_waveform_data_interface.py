#
# Copyright 2022 National Instruments Corporation
#
# SPDX-License-Identifier: MIT
#
"""
Test - Read Waveform Data Interface
"""
# Description:
#   The waveform data interface reads the waveform IQ data in TDMS /MATLAB format
# 	    - waveform (path, name, format)
#       - wireless link parameter map
#
# Test plot the waveform or print its IQ Data
#
import os
import sys
# plot waveform
import matplotlib.pyplot as plt
dir_path = os.path.dirname(__file__)
src_path = os.path.split(dir_path)[0] 
sys.path.insert(0,src_path)

from lib import read_waveform_data_interface

if __name__ == "__main__":

    # waveform format: tdms, matlab, matlab_ieee
    waveform_format = "tdms"
    waveform_path_type =  "relative"

    if waveform_format == "tdms":
        waveform_path = "waveforms/lte/"
        waveform_file_name = "LTE_FDD_DL_10MHz_CC-1_E-UTRA_E-TM2"
        
        if waveform_path_type == "relative":
            dir_path = os.path.dirname(__file__)
            src_path = os.path.split(dir_path)[0] 
            waveform_path = os.path.join(src_path, waveform_path)
        elif waveform_path_type == "absolute":
            pass
        else:
            raise Exception("Error: Unknow waveform path type", waveform_path_type)


        tx_data_complex, waveform_IQ_rate = read_waveform_data_interface.read_waveform_data_tdms(
            waveform_path, waveform_file_name
        )

        plt.specgram(tx_data_complex, Fs=waveform_IQ_rate)
        plt.title(waveform_file_name)
        plt.xlabel("Time (ms)")
        plt.ylabel("Frequency (Hz)")
        plt.show()

    elif waveform_format == "matlab":
        waveform_path = "waveforms/radar/"
        waveform_file_name = "RadarWaveform_BW_2M"
        if waveform_path_type == "relative":
            dir_path = os.path.dirname(__file__)
            src_path = os.path.split(dir_path)[0] 
            waveform_path = os.path.join(src_path, waveform_path)
        elif waveform_path_type == "absolute":
            pass
        else:
            raise Exception("Error: Unknow waveform path type", waveform_path_type)
            
        tx_data_complex = read_waveform_data_interface.read_waveform_data_matlab(
            waveform_path, waveform_file_name
        )
        print(tx_data_complex)

    elif waveform_format == "matlab_ieee":
        waveform_path = "waveforms/wifi/"
        waveform_file_name = "IEEE_tx11ac_legacy_20MHz_80MSps_MCS7_27bytes_1frame"

        if waveform_path_type == "relative":
            dir_path = os.path.dirname(__file__)
            src_path = os.path.split(dir_path)[0] 
            waveform_path = os.path.join(src_path, waveform_path)
        elif waveform_path_type == "absolute":
            pass
        else:
            raise Exception("Error: Unknow waveform path type", waveform_path_type)

        tx_data_complex = read_waveform_data_interface.read_waveform_data_matlab_ieee(
            waveform_path, waveform_file_name
        )
        print(tx_data_complex)