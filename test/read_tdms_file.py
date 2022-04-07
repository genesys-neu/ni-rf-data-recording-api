# read TDMS file
# npTDSM documentation can be found here: https://nptdms.readthedocs.io/en/stable/

import numpy as np
from nptdms import TdmsFile
from nptdms import tdms

# path to TDMS file
tdms_file = TdmsFile.read(
    "/home/agaber/workarea/lti-6g-sw/data-recording-tools/LabVIEW/TDMS Waveform Files/NR_FR1_DL_FDD_SISO_BW-20MHz_CC-1_SCS-30kHz_Mod-64QAM_OFDM_TM3.1.tdms"
)


# get all groups
all_tdms_groups = tdms_file.groups()
print("Example to get all groups: ", all_tdms_groups)

# get all channels
group = tdms_file["waveforms"]
all_group_channels = group.channels()
print("Example to get all group channels: ", all_group_channels)

# get channel data
channel = group["Channel 0"]
channel_data = channel[:]
print("Data length:", len(channel_data))
print("Print the first N I and Q samples: ", channel_data)
tx_data = channel_data[::2] + 1j * channel_data[1::2]
print("Print complex data: ", tx_data)


# Get all properites
channel_properties = channel.properties
print("Example to get all channel properties: ", channel_properties)
NI_RF_IQRate = channel.properties["NI_RF_IQRate"]
NI_RF_SignalBandwidth = channel.properties["NI_RF_SignalBandwidth"]
NI_RF_WaveformType = channel.properties["NI_RF_WaveformType"]
NI_RF_PAPR = channel.properties["NI_RF_PAPR"]
NI_RF_RuntimeScaling = channel.properties["NI_RF_RuntimeScaling"]
dt = channel.properties["dt"]
t0 = channel.properties["t0"]

# Get a channel property
property_value = tdms_file["waveforms"]["Channel 0"].properties["NI_RF_SignalBandwidth"]
print("Example to get channel property value (bandwidth): ", str(property_value))
print("Example to get IQ Rate: ", NI_RF_IQRate)
# ('NI_RF_IQRate', 30720000.0), ('NI_RF_SignalBandwidth', 20000000.0), ('NI_RF_WaveformType', 'InterleavedIQCluster'), ('NI_RF_PAPR', 11.466749575704236), ('NI_RF_RuntimeScaling', -1.5), ('dt', 3.2552083333333335e-08), ('t0', 0.0)])
