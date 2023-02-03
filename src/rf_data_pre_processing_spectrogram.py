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
import argparse
import math
import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as scipysig
from sigmf import SigMFFile, sigmffile

#----------------------------------------------------------------
# Configuration
# 1- specify folder
#dataset_folder = "<<repo>>/recorded-data/"
# 2- specify base filename
#dataset_filename_base = "rx-waveform-td-rec-0-2023_01_31-17_57_41_801"
#---------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Read SigMF metadata and plot time domain and spectrum of recorded IQ data")
    parser.add_argument(
        "--dataset_folder",
        "-f",
        type=str,
        default="recorded-data",
        help="specify folder wherein SigMF file",
    )
    parser.add_argument(
        "--dataset_filename_base",
        "-n",
        type=str,
        default="",
        help="specify name of file to plot",
    )

    args = parser.parse_args()
    if args.dataset_filename_base=="":
        # specify file name for latest meta data file in dataset_folder
        lists=[]
        for file in os.listdir(args.dataset_folder):
            if file.endswith(".sigmf-meta"):
                lists.append(file)

        lists.sort(key=lambda x:os.path.getmtime(os.path.join(args.dataset_folder,x))) 
        if not lists==[]:
            metadata_filename = os.path.join(args.dataset_folder, lists[-1])
            print(f"Ploting latest sigmf file: {metadata_filename}")
        else:
            print(f"Aboarted!! Without finding any sigmf file in: {args.dataset_folder}")
            return
    else:
        # specify file name for meta data
        metadata_filename = os.path.join(args.dataset_folder, args.dataset_filename_base)

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


if __name__ == "__main__":
    main()
