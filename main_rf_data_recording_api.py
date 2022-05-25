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

    ## Get mboard ID and serial number of TX and RX USRPs
    # This extra step is a workaround to solve two limitations in UHD
    # For TX and RX: the master clock rate cannot be changed after opening the session
    # We need to know mBoard ID to select the proper master clock rate in advance
    # For TX based on RFNoc graph: Getting USRP SN is supported in Multi-USRP but not on RFNoC graph
    print("Get Tx and RX USRPs mboards info ...")
    variations_map = rf_data_recording_api.get_usrps_mboard_info(variations_map)
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

        ## Create class list for all TX USRPs, each class has the TX config of related TX signal emitter
        # initialize the list
        txs_data_recording_api_config = []
        for idx in range(1, iteration_general_config["num_tx_usrps"] + 1):
            tx_data_recording_api_config = rf_data_recording_api.TxRFDataRecorderConfig(
                iteration_config, iteration_general_config, idx
            )
            txs_data_recording_api_config.append(tx_data_recording_api_config)

        ## Create class list for all RX USRPs, each class has the RX config of related RX signal acquisition
        # initialize the list
        rxs_data_recording_api_config = []
        for idx in range(1, iteration_general_config["num_rx_usrps"] + 1):
            rx_data_recording_api_config = rf_data_recording_api.RxRFDataRecorderConfig(
                iteration_config, iteration_general_config, idx
            )
            rxs_data_recording_api_config.append(rx_data_recording_api_config)

        ## Get Tx Waveform config
        for idx, tx_data_recording_api_config in enumerate(txs_data_recording_api_config):
            txs_data_recording_api_config[idx] = rf_data_recording_api.read_waveform_config(
                tx_data_recording_api_config
            )

        ## Update rate of Tx and RX USRPs based on selected rate source
        (
            txs_data_recording_api_config,
            rxs_data_recording_api_config,
        ) = rf_data_recording_api.update_rate(
            txs_data_recording_api_config, rxs_data_recording_api_config
        )

        ## Calculate USRP master clockrate based on given rate
        (
            txs_data_recording_api_config,
            rxs_data_recording_api_config,
        ) = rf_data_recording_api.find_proper_master_clock_rate(
            txs_data_recording_api_config, rxs_data_recording_api_config
        )

        ## print iteration config
        rf_data_recording_api.print_iteration_config(
            iteration_config,
            iteration_general_config,
            txs_data_recording_api_config,
            rxs_data_recording_api_config,
        )

        ## Start execution - TX emitters in parallel
        if iteration_general_config["txs_execution"] == "parallel":
            rf_data_recording_api.start_execution_txs_in_parallel(
                txs_data_recording_api_config, rxs_data_recording_api_config
            )
        ## Start execution - TX emitters in sequential
        elif iteration_general_config["txs_execution"] == "sequential":
            rf_data_recording_api.start_execution_txs_in_sequential(
                txs_data_recording_api_config, rxs_data_recording_api_config
            )
        else:
            raise Exception("Error: Unknow tx emitters execution order")



if __name__ == "__main__":
    sys.exit(not main())
