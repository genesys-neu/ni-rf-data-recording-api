# test read json file
##! Data Recording API
# NI
#
# Pre-requests: Install UHD with Python API enabled
#
# created on 2022-03-16
# @author: abdo gaber
import sys
import os
import json
import time
from timeit import default_timer as timer
from pathlib import Path
class TxRFDataRecorderParameters:
    """Top-level TX RFDataRecorder class"""
    def __init__(self):
        # read general parameter set from json config file
        file_path=os.path.split(os.path.dirname(__file__))
        with open(os.path.join(file_path[0], "config_rf_data_recorder.json"), "r") as file:
            config = json.load(file)
            print(config)
        general_config=config["general_config"] 
        tx_config = config["tx_config"]
        # ============= TX Config parameters =============
        # "RF center frequency in Hz, type = float ",
        self.freq=general_config["freq"]
        # "rate of radio block, type = float ",
        self.rate=general_config["rate"]
        # Device args to use when connecting to the USRP, type=str",
        self.args=tx_config["args"] 
        #"radio block to use (e.g., 0 or 1), type = int",
        self.radio_id=tx_config["radio_id"] 
        # "radio channel to use, type = int",
        self.radio_chan=tx_config["radio_chan"]
        # "replay block to use (e.g., 0 or 1), type = int",
        self.replay_id=tx_config["replay_id"]
        #"replay channel to use, type = int ",
        self.replay_chan=tx_config["replay_chan"]
        # "duc channel to use, type = int ",
        self.duc_chan=tx_config["duc_chan"]
        # "antenna selection, type = str",
        self.antenna=tx_config["antenna"]
        # "gain for the RF chain, type = float",
        self.gain=tx_config["gain"]
        # "analog front-end filter bandwidth in Hz, type = float",
        self.bandwidth=tx_config["bandwidth"]
        # "reference source (internal, external, gpsdo, type = str",
        self.reference=tx_config["reference"]
        # "path to TDMS file, type = str ",
        self.waveform_path=tx_config["waveform_path"]
        # "tdms file name, type = str ",
        self.waveform_file_name= tx_config["waveform_file_name"]
        # "number of samples to play (0 for infinite) and based on the number of samples in the loaded waveform, type = str",
        # "Code is not ready to send a specific number of samples, it sends the whole waveform",
        self.nsamps=tx_config["nsamps"]

class RxRFDataRecorderParameters:
    """Top-level RX RFDataRecorder class"""
    def __init__(self):
        # read general parameter set from json config file
        file_path=os.path.split(os.path.dirname(__file__))
        with open(os.path.join(file_path[0], "config_rf_data_recorder.json"), "r") as file:
            config = json.load(file)
            print(config)
        general_config=config["general_config"] 
        rx_config = config["rx_config"]
        # ============= RX Config parameters =============
        # "RF center frequency in Hz, type = float ",
        self.freq=general_config["freq"]
        # "rate of radio block, type = float ",
        self.rate=general_config["rate"]
        # Device args to use when connecting to the USRP, type=str",
        self.args=rx_config["args"]
        # "radio channel to use, type = int",
        self.channels=rx_config["channels"]
        # "antenna selection, type = str",
        self.antenna=rx_config["antenna"]
        # "gain for the RF chain, type = float",
        self.gain=rx_config["gain"]
        # "reference source (internal, external, gpsdo, type = str",
        self.reference=rx_config["reference"]
        # path to store captured rx data
        self.output_file = (Path(__file__).parent / rx_config["output_file"]).resolve()
        # "time duration of IQ data acquestion"
        self.duration = rx_config["duration"]
        # "number of snapshots from RX IQ data aquestion"
        self.nrecords= rx_config["nrecords"]

def main():
    # create rf data recorder
    tx_rf_data_recorder_parameters=TxRFDataRecorderParameters() 
    print(tx_rf_data_recorder_parameters.rate)
    rx_rf_data_recorder_parameters=RxRFDataRecorderParameters() 
    print(rx_rf_data_recorder_parameters.rate)

if __name__ == "__main__":
    sys.exit(not main())

