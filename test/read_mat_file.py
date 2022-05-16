# read mat file
# npTDSM documentation can be found here: https://nptdms.readthedocs.io/en/stable/

import numpy as np
import scipy.io

file = "/home/agaber/workarea/lti-6g-sw/data-recording-tools/uhd/uhd-python-api/waveform-files/matlab_ieee/ieee_tx11ac_legacy_20MHz_80MSps_MCS7_27bytes_1frame/sbb_str.mat"

# option1
mat = scipy.io.loadmat(file) 

print(mat.keys)
data = mat["sbb_str"] 
print(data)
x = data[0][0][0]
print(x)
#print(type(data))
#print(data.ndim)
#print(data.item)
#print(len(data))
x= data[0].tolist()[0] 
y= x[0,:] 
print(x.shape)

print(len(x))
print(y)

# Option2
#import h5py
#f = h5py.File(file,'r')
#print(f.keys())
#data = f.get('data/variable1')
#data = np.array(data) # For converting to a NumPy array
# option3
#mat = np.loadtxt(file)
#option4
#from mat4py import loadmat
#data = loadmat(file)
# option5
#import numpy as np
#data = np.loadtxt(file)

from pathlib import Path
def read_mat_ieee_waveform_data(path, file):
    # Open the file
    file_path = (Path(__file__).parent /path /str(file)).resolve() #+ str(file)
    print("file path", file_path)
    filename = str(file_path) + "/sbb_str.mat"
    print(filename)
    mat_data = scipy.io.loadmat(filename)
    # get data  
    data = mat_data["sbb_str"]
    tx_data_complex  = data[0][0][0]

    return tx_data_complex#, wavform_IQ_rate


path="waveform-files/matlab_ieee/"
file="ieee_tx11ac_legacy_20MHz_80MSps_MCS7_27bytes_1frame"
waveform_format_type="mat_ieee"
tx_data_complex = read_mat_ieee_waveform_data(path, file)