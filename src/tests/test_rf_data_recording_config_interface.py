#
# Copyright 2022 National Instruments Corporation
#
# SPDX-License-Identifier: MIT
#
"""
Test - RF Data Recording API Configuration Interface
"""
# Description:
#   The configuration interface reads the configuration file and creates the variation map by doing a cross product over all possible values. Each TX and RX has own list of parameters. Some TX parameters are common for all Tx USRPs, and they are listed under common transmitters config section. The resulting variation map has four sections:
# 	    - General configuration
# 	    - TX USRP configuration
# 	    - Common Tx USRPs configuration
# 	    - RX USRP configuration
#
# Test prints the resulting variation map using both YAML or JSON Config file
#

import os
import sys
dir_path = os.path.dirname(__file__)
src_path = os.path.split(dir_path)[0] 
sys.path.insert(0,src_path)
from lib import rf_data_recording_config_interface


if __name__ == "__main__":

    rf_data_acq_config_file = "config/config_rf_data_recording_api.json"

    variations_map1 = rf_data_recording_config_interface.generate_rf_data_recording_configs(rf_data_acq_config_file)

    rf_data_acq_config_file = "config/config_rf_data_recording_api.yaml"

    variations_map2 = rf_data_recording_config_interface.generate_rf_data_recording_configs(rf_data_acq_config_file)
