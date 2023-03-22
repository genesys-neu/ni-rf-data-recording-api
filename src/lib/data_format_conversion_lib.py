#
# Copyright 2022 National Instruments Corporation
#
# SPDX-License-Identifier: MIT
#
"""
Data format conversion Lib
"""
# Description:
#   Change the data format of a given varible based on the need
#
# Change numerical string with k, M, or G to float number
def si_unit_string_converstion_to_float(x):
    si_list = ["k", "M", "G"]
    if any(letter in x for letter in si_list):
        if "k" in x:
            x_str = x.replace("k", "000")
        elif "M" in x:
            x_str = x.replace("M", "000000")
        elif "G" in x:
            x_str = x.replace("G", "000000000")
        value = float(x_str)
    elif "m" in x:
        x_str = x.replace("m", "")
        value = float(x_str) / 1000
    else:
        value = float(x)

    return float(value)


# string to boolean
def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise Exception("ERROR: Boolean value expected.")
