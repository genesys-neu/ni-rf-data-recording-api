#
# Copyright 2022 National Instruments Corporation
#
# SPDX-License-Identifier: MIT
#
# Read TX waveform file in TDMS format and plot its spectrogram

import os
import sys
dir_path = os.path.dirname(__file__)
src_path = os.path.split(dir_path)[0] 
sys.path.insert(0,src_path)
from lib import read_waveform_data_interface

import matplotlib.pyplot as plt

# path to TDMS file
waveform_path = "waveforms/lte/"
waveform_file_name = "LTE_FDD_DL_10MHz_CC-1_E-UTRA_E-TM2"

waveform_path = os.path.join(src_path, waveform_path)
tx_data_complex, waveform_IQ_rate = read_waveform_data_interface.read_waveform_data_tdms(
            waveform_path, waveform_file_name
        )

plt.specgram(tx_data_complex, Fs=waveform_IQ_rate)
plt.title(waveform_file_name )
plt.xlabel("Time (ms)")
plt.ylabel("Frequency (Hz)")
plt.show()

