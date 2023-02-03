#
# Copyright 2022 National Instruments Corporation
#
# SPDX-License-Identifier: MIT
#
# Simple test to load sigmf meta data file and print its main sections

import sigmf
import os
import sys
dir_path = os.path.dirname(__file__)
src_path = os.path.split(dir_path)[0] 
sys.path.insert(0,src_path)

recorded_data_path = "recorded-data"
recorded_data_file_name = "rx-waveform-td-rec-0-2023_01_31-17_57_41_801.sigmf"

metadata_filename = os.path.join(args.dataset_folder, args.dataset_filename_base)
handle = sigmf.sigmffile.fromfile(metadata_filename))
#handle = sigmf.sigmffile.fromfile("/home/user/workarea/recorded-data/rx-waveform-td-rec-0-2023_01_31-17_57_41_801.sigmf")
print(handle.read_samples())  # returns all timeseries data
handle.get_global_info()  # returns 'global' dictionary
print(handle.get_global_info)
handle.get_captures()  # returns list of 'captures' dictionaries
print(handle.get_captures)
handle.get_annotations()  # returns list of all annotations
print(handle.get_annotations)
