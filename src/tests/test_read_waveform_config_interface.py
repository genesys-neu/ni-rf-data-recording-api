#
# Copyright 2022 National Instruments Corporation
#
# SPDX-License-Identifier: MIT
#
"""
Test - Read Waveform Config Interface
"""
# Description:
#   The waveform configuration interface reads the configuration file and maps the parameter name of waveform creator to SigMF meta data
# 	    -   waveform (path, name, format)
#       -   wireless link parameter map
#
# Test prints the waveform config
# Select the parameters in the class
#
import os
import sys
dir_path = os.path.dirname(__file__)
src_path = os.path.split(dir_path)[0] 
sys.path.insert(0,src_path)

from lib import read_waveform_config_interface

if __name__ == "__main__":

    # local class for testing
    class TxRFDataRecorderConfig:
        """Tx RFDataRecorder Config class"""

        def __init__(self):
            # ============= TX Config parameters =============
            # waveform file name
            # nr
            #self.waveform_file_name = "NR_FR1_UL_All_SISO_BW-20MHz_CC-1_SCS-30kHz_Mod-64QAM_OFDM_enabled_PTRS"
            # lTE
            #self.waveform_file_name = ("LTE_TDD_UL_RMC_A2321_4_2_10MHz_6_7")
            # Radar
            self.waveform_file_name = "RadarWaveform_BW_1428k"
            # Wifi
            #self.waveform_file_name = "IEEE_tx11ac_legacy_20MHz_80MSps_MCS7_27bytes_1frame"
            # Path to waveform file
            self.waveform_path = "waveforms/wifi/"
            # "possible values: tdms, matlab_ieee, type = str ",
            self.waveform_format = "matlab"
            # Define dictionary for tx wavform config
            waveform_config = {}
            self.waveform_config = waveform_config

    wireless_link_parameter_map = "wireless_link_parameter_map.yaml"
    tx_data_recording_api_config = TxRFDataRecorderConfig()
    
    tx_data_recording_api_config = read_waveform_config_interface.read_tx_waveform_config(
        tx_data_recording_api_config, wireless_link_parameter_map
    )
    waveform_config = tx_data_recording_api_config.waveform_config
    print(waveform_config)
    # attrs = vars(waveform_config)
    # print(', '.join("%s: %s" % item for item in attrs.items()))
