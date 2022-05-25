## Read waveform data config in matlab format for IEEE waveform generator
import csv
from pathlib import Path
import re

path = "../waveform-files/matlab/"
file = "RadarWaveform_Sample1"


def initalize_waveform_config():
    waveform_config = {
        "standard": "",
        "freqeuncy_range": "",
        "link_direction": "",
        "duplexing": "",
        "multiplexing": "",
        "multiple_access": "",
        "spreading": "",
        "bandwidth": "",
        "rate": "",
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
    return waveform_config


def freq_string_to_float(x):
    if "k" in x:
        x_str = x.replace("k", "000")
    elif "M" in x:
        x_str = x.replace("M", "000000")
    elif "G" in x:
        x_str = x.replace("G", "000000000")
    else:
        x_str = x
    return float(x_str)


def read_mat_ieee_waveform_config(path, file):
    folder_path = (Path(__file__).parent / path).resolve()
    # The mat waveform config file is saved with the same name of waveform but in csv
    file_path = str(folder_path) + "/" + file + ".csv"
    with open(file_path, "r") as file_p:
        csvreader = csv.reader(filter(lambda row: row[0] != "#", file_p))
        cfg_dict = {}
        for row in csvreader:
            cfg_dict[row[0]] = row[1]
    print(type(cfg_dict))
    # create harmonized dictionary
    waveform_config = initalize_waveform_config()
    waveform_config["standard"] = cfg_dict["standard"]
    x = waveform_config["standard"]
    print(type(x))
    waveform_config["bandwidth"] = freq_string_to_float(cfg_dict["bandwidth"])
    waveform_config["rate"] = freq_string_to_float(cfg_dict["rate"])
    waveform_config["n_frames"] = cfg_dict["n_frames"]
    return waveform_config


waveform_config = read_mat_ieee_waveform_config(path, file)
print(waveform_config)
