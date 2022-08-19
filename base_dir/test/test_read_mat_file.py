# read mat file
import numpy as np
import scipy.io

from pathlib import Path


def read_mat_ieee_waveform_data(path, file):
    # Open the file
    file_path = (Path(__file__).parent / path / str(file)).resolve()  # + str(file)
    print("file path", file_path)
    filename = str(file_path) + "/sbb_str.mat"
    print(filename)
    mat_data = scipy.io.loadmat(filename)
    print(mat_data)
    print("Keys: ", mat_data.keys)
    # get data
    data = mat_data["sbb_str"]
    tx_data_complex = data[0][0][0]

    return tx_data_complex  # , wavform_IQ_rate


path = "../waveform-files/matlab_ieee/"
file = "IEEE_tx11ac_legacy_20MHz_80MSps_MCS7_27bytes_1frame"
waveform_format_type = "mat_ieee"
tx_data_complex = read_mat_ieee_waveform_data(path, file)
