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
from queue import Queue
import argparse

# import related functions
import rf_data_recording_api_def
import sync_settings

# To print colours
from termcolor import colored


def main(rf_data_acq_config_file):

    ## Get RF Data Collection API Configuration
    # given as input

    # Get Time Stamp for statistics
    start_time = time.time()
    # Create RF data recording API class and load Config
    ## Create all configuration variations - cross product
    print("Load RF Data recorder config ...")
    print("Create configuration variations ...")
    rf_data_recording_api = rf_data_recording_api_def.RFDataRecorderAPI(rf_data_acq_config_file)
    variations_map = rf_data_recording_api.variations_map
    print("")

    # Read general config, it has only a single list
    general_config = variations_map.general_config.iloc[0]

    # get default wavefrom config
    default_waveform_config_file = general_config["waveform_config_file"]
    # get enabel console logging flag
    enable_console_logging = rf_data_recording_api_def.RFDataRecorderAPI.str2bool(
        general_config["enable_console_logging"]
    )

    ## Get Hw type, subtype and HW ID of TX and RX stations
    # For USRP:
    # HW type = USRP type, mboard ID, i.e. USRP X310
    # HW subtype = USRP daughterboard type
    # HW seid = USRP serial number
    # This extra step is a workaround to solve two limitations in UHD
    # For TX and RX: the master clock rate cannot be changed after opening the session
    # We need to know mBoard ID to select the proper master clock rate in advance
    # For TX based on RFNoc graph: Getting USRP SN is supported in Multi-USRP but not on RFNoC graph
    print("Get Tx and RX stations HW info ...")
    variations_map = rf_data_recording_api.get_hardware_info(variations_map, enable_console_logging)
    print("")

    # Create que to store rx data in bytes
    # User will know the data size written to the memory
    rx_data_nbytes_que = Queue()

    for i in range(len(variations_map.variations_product)):
        print("Variation Number: ", i)

        ##  Initlize sync settings
        sync_settings.init()
        # print sync status
        if enable_console_logging:
            print(
                "Sync Status: Start Data Acquestion called = ",
                sync_settings.start_rx_data_acquisition_called,
                " Stop Tx Signal called = ",
                sync_settings.stop_tx_signal_called,
            )

        ## Get TX and RX RF Data Recorder Config
        iteration_config = variations_map.variations_product.iloc[i]

        ## Create class list for all TX USRPs, each class has the TX config of related TX signal emitter
        # initialize the list
        txs_data_recording_api_config = []
        for idx in range(1, general_config["num_tx_usrps"] + 1):
            tx_data_recording_api_config = rf_data_recording_api.TxRFDataRecorderConfig(
                iteration_config, general_config, idx
            )
            txs_data_recording_api_config.append(tx_data_recording_api_config)

        ## Create class list for all RX USRPs, each class has the RX config of related RX signal acquisition
        # initialize the list
        rxs_data_recording_api_config = []
        for idx in range(1, general_config["num_rx_usrps"] + 1):
            rx_data_recording_api_config = rf_data_recording_api.RxRFDataRecorderConfig(
                iteration_config, general_config, idx
            )
            rxs_data_recording_api_config.append(rx_data_recording_api_config)

        ## Get Tx Waveform config
        for idx, tx_data_recording_api_config in enumerate(txs_data_recording_api_config):
            txs_data_recording_api_config[idx] = rf_data_recording_api.read_waveform_config(
                tx_data_recording_api_config,
                default_waveform_config_file,
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
        if enable_console_logging:
            rf_data_recording_api.print_iteration_config(
                iteration_config,
                general_config,
                txs_data_recording_api_config,
                rxs_data_recording_api_config,
            )

        ## Get API Operation mode
        api_operation_mode = general_config["API_operation_mode"]

        # For Rx-only mode:
        if (
            api_operation_mode == rf_data_recording_api_def.RFDataRecorderAPI.API_operation_modes[1]
        ):  # Rx only mode
            rf_data_recording_api.start_rxs_execution(
                txs_data_recording_api_config,
                rxs_data_recording_api_config,
                general_config,
                rx_data_nbytes_que,
            )

        ### Start execution - TX emitters in parallel
        # TX-only mode or Tx-Rx mode
        else:
            if general_config["txs_execution"] == "parallel":
                rf_data_recording_api.start_execution_txs_in_parallel(
                    txs_data_recording_api_config,
                    rxs_data_recording_api_config,
                    api_operation_mode,
                    general_config,
                    rx_data_nbytes_que,
                )
            ## Start execution - TX emitters in sequential
            elif general_config["txs_execution"] == "sequential":
                rf_data_recording_api.start_execution_txs_in_sequential(
                    txs_data_recording_api_config,
                    rxs_data_recording_api_config,
                    api_operation_mode,
                    general_config,
                    rx_data_nbytes_que,
                    enable_console_logging,
                )
            else:
                raise Exception("Error: Unknow tx emitters execution order")

    # Get end time
    end_time = time.time()
    time_elapsed = end_time - start_time
    time_elapsed_s = int(time_elapsed * 1000) * 1 / 1000
    print("")
    print(
        "Total elapsed time of getting rx samples and writing data and meta data files of ",
        i + 1,
        "config variations:",
        colored(time_elapsed_s, "yellow"),
        "s",
    )
    total_rx_data_nbytes = 0
    while not rx_data_nbytes_que.empty():
        total_rx_data_nbytes = total_rx_data_nbytes + rx_data_nbytes_que.get()

    print(
        "Total size of Rx Data: ",
        colored(total_rx_data_nbytes / 1e6, "yellow"),
        "MByte",
    )


if __name__ == "__main__":
    # flag to be disabled for execution from IDE
    enable_cli_args = True

    if enable_cli_args:
        # parse arguments
        parser = argparse.ArgumentParser(description="NI RF Data Collection API")
        parser.add_argument(
            "--main_config",
            type=str,
            default="config_rf_data_recording_api.yaml",
            help="RF data collection API config file",
        )
        args = parser.parse_args()

        main_config = args.main_config
    else:
        # use default config file
        main_config = "config_rf_data_recording_api.yaml"

    # start main program
    main(main_config)
