##! Data Recording API
#
# Copyright 2022 NI Dresden
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Pre-requests: Install UHD with Python API enabled
#
import sys
import time
from timeit import default_timer as timer
from pathlib import Path
from operator import index
import numpy as np
from pandas import DataFrame, merge
# importing the threading module
import threading
from multiprocessing.sharedctypes import Value
# import related functions
import rf_data_recording_api_def
import run_rf_replay_data_transmitter
import run_rf_data_recorder
import sync_settings

def main():

    ## Get RF Data Collection API Configuration
    config_file_name = "config_rf_data_recording_api.json"

    # Create RF data recording API class and load Config
    print("Load RF Data recorder config ...")
    rf_data_recording_api = rf_data_recording_api_def.RFDataRecorderAPI(config_file_name)

    ## Create all configuration variations - cross product
    print("Create configuration variations ...")
    variations_map = rf_data_recording_api.CreateVariationsMap(rf_data_recording_api.config)
    print("")

    # Get serial numbers of TX USRPs -  This extra step is a workaround
    # Getting USRP SN is supported in Multi-USRP but not on RFNoC graph
    tx_usrp_serial_numbers_list = rf_data_recording_api.get_usrp_serial_number()
    print("TX USRPs Serial Numbers: ")
    print(tx_usrp_serial_numbers_list)
    print("")

    for i in range(len(variations_map.variations_product)):
        print("Variation Number: ", i)

        ##  Initlize sync settings
        sync_settings.init()
        print(
            "Sync Status: ",
            sync_settings.start_rx_data_acquisition_called,
            " ",
            sync_settings.stop_tx_signal_called,
        )

        ## Get TX and RX RF Data Recorder Config
        iteration_config = variations_map.variations_product.iloc[i]
        # iteration general config has only a single list
        iteration_general_config = variations_map.general_config_dic.iloc[0]
        print("Iteration config: ")
        print(iteration_config)
        print("Iteration general config: ")
        print(iteration_general_config)

        ## Create TX and RX RF Config classes
        tx_data_recording_api_config = rf_data_recording_api.TxRFDataRecorderConfig(
            iteration_config, iteration_general_config
        )
        rx_data_recording_api_config = rf_data_recording_api.RxRFDataRecorderConfig(
            iteration_config, iteration_general_config
        )

        # Store TX USRP serial number in TX config to be stored in meta-data as TX ID
        tx_data_recording_api_config.usrp_serial_number = (
            rf_data_recording_api.handle_tx_usrp_serial_number(
                tx_usrp_serial_numbers_list, tx_data_recording_api_config.args
            )
        )

        # Calculate USRP master clockrate based on given rate
        tx_data_recording_api_config.args = rf_data_recording_api.calculate_master_clock_rate(
            tx_data_recording_api_config.args
        )
        rx_data_recording_api_config.args = rf_data_recording_api.calculate_master_clock_rate(
            rx_data_recording_api_config.args
        )

        ## Create multi threads
        tx_proc = threading.Thread(
            target=run_rf_replay_data_transmitter.rf_replay_data_transmitter,
            args=(tx_data_recording_api_config,),
        )
        rx_proc = threading.Thread(
            target=run_rf_data_recorder.rf_data_recorder,
            args=(
                rx_data_recording_api_config,
                tx_data_recording_api_config,
            ),
        )

        ## Start threads
        # starting thread 1
        tx_proc.start()
        # starting thread 2
        rx_proc.start()

        # wait until thread 1 is completely executed
        tx_proc.join()
        # wait until thread 2 is completely executed
        rx_proc.join()
        # settling time
        time.sleep(0.5)

if __name__ == "__main__":
    sys.exit(not main())
