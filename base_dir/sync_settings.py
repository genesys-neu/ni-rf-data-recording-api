#
# Copyright 2022 National Instruments Corporation
#
# SPDX-License-Identifier: MIT
#
"""
TX and Rx Data Acquition Sync
"""
# Description:
#   define global variables to sync betweem Tx and Rx start and stop execution
#


def init():
    # start Rx data acquestion if TX signal is on the air
    global start_rx_data_acquisition_called
    # stop TX data transmission if RX data aquestion is done
    global stop_tx_signal_called
    # TX USRP Serial Number
    global tx_usrp_serial_number
    stop_tx_signal_called = False
    start_rx_data_acquisition_called = False
