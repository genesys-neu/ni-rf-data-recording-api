# Read TDMS file
# npTDSM documentation can be found here: https://nptdms.readthedocs.io/en/stable/

import numpy as np
from nptdms import TdmsFile
import matplotlib.pyplot as plt

## Read waveform data in TDSM format
def read_tdms_waveform_data(path, file):

    # Open the file
    tdms_file = TdmsFile.read(str(path) + str(file) + ".tdms")

    # get all channels
    group = tdms_file["waveforms"]
    # get channel data
    channel = ""
    if "Channel 0" in group:
        channel = group["Channel 0"]
    elif "segment0/channel0" in group:
        channel = group["segment0/channel0"]
    if not channel:
        raise Exception("ERROR: Unkown channel name of a given TDMS Waveform")

    wavform_IQ_rate = channel.properties["NI_RF_IQRate"]

    tx_data_float = channel[:]
    tx_data_complex = tx_data_float[::2] + 1j * tx_data_float[1::2]
    return tx_data_complex, wavform_IQ_rate


# path to TDMS file
waveform_path = "/home/user/workarea/lti-6g-sw/lti-6g-sw/data-recording-tools/uhd/uhd-python-api/waveform-files/tdms/"
waveform_file_name = "LTE_FDD_DL_10MHz_CC-1_E-UTRA_E-TM2"

tx_data_complex, waveform_IQ_rate = read_tdms_waveform_data(
            waveform_path, waveform_file_name
        )

plt.specgram(tx_data_complex, Fs=waveform_IQ_rate)
plt.title(waveform_file_name )
plt.xlabel("Time (ms)")
plt.ylabel("Frequency (Hz)")
plt.show()

