# read mat file

import numpy as np
import scipy.io


from pathlib import Path


def read_matlab_waveform_data(path, file):
    # Open the file
    file_path = (Path(__file__).parent / path / str(file)).resolve()  # + str(file)
    print("file path: ", file_path)
    filename = str(file_path) + ".mat"
    print("file_name:", filename)
    mat_data = scipy.io.loadmat(filename)
    print(mat_data)
    print("Keys: ", mat_data.keys)
    # get data
    data = mat_data["waveform"]
    tx_data_complex = data
    print(type(data))

    return tx_data_complex  # , wavform_IQ_rate


path = "../waveform-files/matlab/"
file = "RadarWaveform_BW_1428k"
waveform_format_type = "matlab"
tx_data_complex = read_matlab_waveform_data(path, file)
print(len(tx_data_complex))
