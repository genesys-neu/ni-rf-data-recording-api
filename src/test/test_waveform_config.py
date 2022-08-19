import os
import yaml
from timeit import default_timer as timer
from pathlib import Path
from multiprocessing.sharedctypes import Value
from operator import index
from wave import Wave_write
import numpy as np
import pandas as pd
from sympy import var


waveform_config = {
            "standard": "",
            "frequency_range": "",
            "link_direction": "",
            "duplexing": "",
            "multiplexing": "",
            "multiple_access": "",
            "spreading": "",
            "bandwidth": 0.0,
            "rate": 0.0,
            "MCS": "",
            "modulation": "",
            "modulation_order": "",
            "code_rate": "",
            "subcarrier_spacing": "",
            "n_frames": "",
            "test_model": "",
            "carrier_CC_index": "",
            "ssb_config_set": "",
            "ssb_periodicity": "",
            "IEEE_MAC_frame_type": "",
            "IEEE_PSDU_length_bytes": "",
        }
print(waveform_config)
# read general parameter set from yaml config file
with open(os.path.join(os.path.dirname(__file__), "default_waveform_config.yaml"), "r") as file:
    rf_data_acq_config = yaml.load(file, Loader=yaml.Loader)
print(rf_data_acq_config)

if waveform_config == rf_data_acq_config:
    print("valid")
