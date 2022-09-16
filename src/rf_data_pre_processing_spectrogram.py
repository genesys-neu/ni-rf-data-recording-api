#
# Copyright 2022 National Instruments Corporation
#
# SPDX-License-Identifier: MIT
#
"""
RF Data Pre-Processing API
"""
# Description:
#   Used to plot the spectrogram of recorded IQ data
#
# Parameters:
#   dataset_folder: specify path to folder of recorded data
#   dataset_filename_base: specify base filename
#
import os
import math
import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as scipysig
from sigmf import SigMFFile, sigmffile

#----------------------------------------------------------------
# Configuration
# 1- specify folder
dataset_folder = "/home/user/workarea/recorded-data"
# 2- specify base filename
dataset_filename_base = "rx_data_record_2022_09_16-16_17_07_620"
#---------------------------------------------------------------

# specify file name for meta data
metadata_filename = os.path.join(dataset_folder, dataset_filename_base)

# load a dataset meta data
metadata = sigmffile.fromfile(metadata_filename)

# Get some metadata and all annotations
sample_rate = metadata.get_global_field(SigMFFile.SAMPLE_RATE_KEY)
sample_count = metadata.sample_count
signal_duration = sample_count / sample_rate
annotations = metadata.get_annotations()

# Iterate over annotations
for idx, annotation in enumerate(annotations):
    annotation_start_idx = annotation[SigMFFile.START_INDEX_KEY]
    annotation_length = annotation[SigMFFile.LENGTH_INDEX_KEY]
    annotation_comment = annotation.get(SigMFFile.COMMENT_KEY, "[annotation {}]".format(idx))

    # Get capture info associated with the start of annotation
    capture = metadata.get_capture_info(annotation_start_idx)
    freq_center = capture.get(SigMFFile.FREQUENCY_KEY, 0)
    freq_min = freq_center - 0.5 * sample_rate
    freq_max = freq_center + 0.5 * sample_rate

    # Get frequency edges of annotation (default to edges of capture)
    freq_start = annotation.get(SigMFFile.FLO_KEY)
    freq_stop = annotation.get(SigMFFile.FHI_KEY)

# load data set
dataset = metadata.read_samples().view("complex64").flatten()
# NOTE: dtype should be taken from meta-data but currently cf64-le is not supported by sigmf
# data = dataset.flatten()

plt.specgram(dataset, Fs=sample_rate, Fc=freq_center)
plt.title("Spectrogram")
plt.xlabel("Time (ms)")
plt.ylabel("Frequency (Hz)")
plt.show()
