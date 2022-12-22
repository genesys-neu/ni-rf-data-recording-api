#
# Copyright 2022 National Instruments Corporation
#
# SPDX-License-Identifier: MIT
#
## Description:
#   Used to plot time domain and freqeuncy domain of recorded IQ data
#
# Parameters:
#   dataset_folder: specify path to folder of recorded data
#   dataset_filename_base: specify base filename
#
#  Load SigMF data set and plot it based on Config in Meta-data

import os
import numpy as np
import scipy.signal as scipysig
# import matplotlib as mpl
import matplotlib.pyplot as plt
from sigmf import SigMFFile, sigmffile

#----------------------------------------------------------------
# Configuration
# 1- specify folder
dataset_folder = "/home/user/workarea/recorded-data"
# 2- specify base filename
dataset_filename_base = "rx-waveform-td-rec-0-2022_12_22-10_49_41_418"
#---------------------------------------------------------------

# initalize local variables
plot_enabled = True
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
    
    data_type = "complex64" #signal_detail["data_type"]

# load data set
dataset = metadata.read_samples().view(data_type).flatten()
# NOTE: dtype should be taken from meta-data but currently cf64-le is not supported by sigmf

# plot data
if plot_enabled == True:
    # plot  signal - for debugging
    plot_signal = dataset.flatten()
    plt.figure(1)
    plt.subplot(211)
    sig_time_base_ms = np.arange(1, plot_signal.size + 1) * 1e3 / sample_rate
    plt.plot(sig_time_base_ms, np.real(plot_signal))
    plt.title("Time domain signal")
    plt.xlabel("t [ms]")
    plt.ylabel("Re\{x(t)\}")
    plt.grid()
    plt.subplot(212)
    f, Pxx_den = scipysig.periodogram(
        plot_signal, fs=sample_rate, nfft=None, window="hamming", scaling="spectrum"
    )
    plt.plot(f, 10*np.log10(Pxx_den))
    plt.title("Frequency domain signal (Spectrum)")
    plt.xlabel("frequency [Hz]")
    plt.ylabel("PSD")
    plt.grid()
    plt.show()
