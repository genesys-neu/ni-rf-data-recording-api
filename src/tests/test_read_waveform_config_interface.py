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
sys.path.insert(0, src_path)

from lib import read_waveform_config_interface

if __name__ == "__main__":

    # local class for testing
    class TxRFDataRecorderConfig:
        """Tx RFDataRecorder Config class"""

        def __init__(self):
            # ============= TX Config parameters =============
            self.waveform_path_type = "relative"
            # waveform file name
            standard = "5gnr"
            if standard == "5gnr":
                # nr
                self.waveform_generator = "5gnr_ni_rfmx_rfws"
                self.waveform_file_name = (
                    "NR_FR1_DL_FDD_SISO_BW-10MHz_CC-1_SCS-30kHz_OFDM_TM2"
                )
                # self.waveform_file_name = "NR_FR1_UL_All_SISO_BW-20MHz_CC-1_SCS-30kHz_Mod-64QAM_OFDM_enabled_PTRS"
                self.waveform_path = "waveforms/nr/"
                # "possible values: tdms, matlab_ieee, matlab, type = str ",
                self.waveform_format = "tdms"

            elif standard == "lte":
                # lte
                self.waveform_generator = "lte_ni_rfmx_rfws"
                # self.waveform_file_name = "LTE_FDD_DL_10MHz_CC-1_E-UTRA_E-TM2"
                self.waveform_file_name = "LTE_FDD_UL_RMC_A2211_1_10MHz-6_5_1"
                self.waveform_path = "waveforms/lte/"
                # "possible values: tdms, matlab_ieee, matlab, type = str ",
                self.waveform_format = "tdms"
            elif standard == "radar":
                # radar
                self.waveform_generator = "radar_nist"
                self.waveform_file_name = "RadarWaveform_BW_2M"
                self.waveform_path = "waveforms/radar/"
                # "possible values: tdms, matlab_ieee, matlab, type = str ",
                self.waveform_format = "matlab"
            elif standard == "wifi":
                # wifi
                self.waveform_generator = "802.11_ieee_gen_matlab"
                self.waveform_file_name = "IEEE_tx11ac_legacy_20MHz_80MSps_MCS7_27bytes_1frame"
                self.waveform_path = "waveforms/wifi/"
                # "possible values: tdms, matlab_ieee, matlab, type = str ",
                self.waveform_format = "matlab_ieee"

            if self.waveform_path_type == "relative":
                dir_path = os.path.dirname(__file__)
                src_path = os.path.split(dir_path)[0]
                self.waveform_path = os.path.join(src_path, self.waveform_path)
            elif self.waveform_path_type == "absolute":
                pass
            else:
                raise Exception("Error: Unknow waveform path type", self.waveform_path_type)
            # Define dictionary for tx waveform config
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
