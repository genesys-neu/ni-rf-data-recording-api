## Read waveform data config in matlab format for IEEE waveform generator
import csv
from pathlib import Path
import re

path = "../waveform-files/matlab_ieee/"
file = "IEEE_tx11ac_legacy_20MHz_80MSps_MCS7_27bytes_1frame"


def read_mat_ieee_waveform_config(path, file):
    folder_path = (Path(__file__).parent / path / str(file)).resolve()
    file_path = str(folder_path) + "/cfg.csv"

    with open(file_path, "r") as file_p:
        csv_dicts = csv.DictReader(filter(lambda row: row[0] != "#", file_p), delimiter=";")
        print("cfg dict", csv_dicts)
        # only one row of values is expected
        for row in csv_dicts:
            cfg_dict = row
    print("cfg dict", cfg_dict)
    # Modulation schemes: lookup table as a constant dictionary:
    modulation_schemes = {"1": "BPSK", "2": "QPSK", "4": "16QAM", "6": "64QAM", "8": "256QAM"}
    if cfg_dict["mods"] in modulation_schemes.keys():
        cfg_dict["mods"] = modulation_schemes[cfg_dict["mods"]]
    else:
        raise Exception("ERROR: Unsupported modulation scheme")

    # create harmonized dictionary
    waveform_config = {}
    waveform_config["standard"] = file
    waveform_config["bandwidth"] = float(cfg_dict["BW_str"]) * 1e6
    waveform_config["MCS"] = cfg_dict["mcs"]
    waveform_config["code_rate"] = cfg_dict["crate"]
    waveform_config["mod_class"] = cfg_dict["mods"]
    waveform_config["subcarrier_spacing"] = ""
    waveform_config["MAC_frame_type"] = cfg_dict["format"]
    waveform_config["PSDU_length_bytes"] = cfg_dict["PSDU_length"]
    # multiplexing
    waveform_config["multiplexing"] = "OFDM"
    # multiple access
    waveform_config["multiple_access"] = ""

    return waveform_config


waveform_config = read_mat_ieee_waveform_config(path, file)
print(waveform_config)
