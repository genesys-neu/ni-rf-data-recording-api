#
# Copyright 2022 National Instruments Corporation
#
# SPDX-License-Identifier: MIT
#
# Simple test to load sigmf meta data file and print its main sections

import sigmf

handle = sigmf.sigmffile.fromfile("/home/agaber/workarea/recorded-data/rx_data_record_2022_08_23-13_31_47_810.sigmf")
print(handle.read_samples())  # returns all timeseries data
handle.get_global_info()  # returns 'global' dictionary
print(handle.get_global_info)
handle.get_captures()  # returns list of 'captures' dictionaries
print(handle.get_captures)
handle.get_annotations()  # returns list of all annotations
print(handle.get_annotations)
