## Read waveform data config in matlab format for IEEE waveform generator
import csv
from pathlib import Path
import re

path="waveform-files/matlab_ieee/"
file="IEEE_tx11ac_legacy_20MHz_80MSps_MCS7_27bytes_1frame"

def read_mat_ieee_waveform_config(path, file):
    folder_path = (Path(__file__).parent /path /str(file)).resolve()
    file_path = str(folder_path) + "/cfg.csv"

    with open(file_path, "r") as file_p:
        csvreader = csv.reader(file_p)
        header = next(csvreader)
        rows = header 
        for row in csvreader:
            rows.append(row)

    cfg_list =[] 
    for row in rows:
        if row[0][0]  !="#":
            cfg_list.append(row)

    pattern = r';'
    cfg_list_split =[] 
    for row in cfg_list:
        cfg_list_split.append(re.split(pattern,row[0] ))

    cfg_dict = {} 
    header = cfg_list_split[0]
    values = cfg_list_split[1]

    for index in range(len(header)):
        cfg_dict[header[index]]= values[index]
    
    cfg_dict["BW"] = float(cfg_dict["BW_str"]) * 1e6
    if cfg_dict["mods"] == "1":
        cfg_dict["mods"] = "BPSK"
    elif cfg_dict["mods"] == "2":
        cfg_dict["mods"] = "QPSK"
    elif cfg_dict["mods"] == "4":
        cfg_dict["mods"] = "16QAM"
    elif cfg_dict["mods"] == "6":
        cfg_dict["mods"] = "64QAM"
    elif cfg_dict["mods"] == "8":
        cfg_dict["mods"] = "256QAM"  
    else: 
        print("ERROR: Not supported modulation scheme order")
    
    # create harmonized dictionary
    waveform_config  = {}
    waveform_config["Standard"] = file
    waveform_config["Bandwidth"] = cfg_dict["BW"]
    waveform_config["MCS"]= cfg_dict["mcs"] 
    waveform_config ["code_rate"]= cfg_dict["crate"]
    waveform_config ["MOD"]= cfg_dict["mods"]
    waveform_config["SCS"] =""
    waveform_config["MAC_frame_type"] = cfg_dict["format"]     
    waveform_config ["PSDU_length_bytes"]= cfg_dict["PSDU_length"]
    # multiplexing
    waveform_config["multiplexing"] = "OFDM"
    # multiple access
    waveform_config["multiple_access"] = "" 
    
    return waveform_config
waveform_config = read_mat_ieee_waveform_config(path, file)
print(waveform_config)


