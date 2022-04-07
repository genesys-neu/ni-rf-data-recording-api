##! Write RX Data to a file in SigMF Format
#
# Copyright 2022 NI Dresden
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# To write Data to sigmf file
import sigmf
import datetime as dt
from sigmf import SigMFFile
from sigmf.utils import get_data_type_str
# To save to specific path
import os
from pathlib import Path
# To use data time
from datetime import datetime

def write_rx_recorded_data_in_sigmf(rx_data, rx_args, tx_args):
        # Write recorded data to file
        # Get time stamp
        time_stamp_micro_sec = datetime.now().strftime("%Y_%m_%d-%H_%M_%S_%f")
        time_stamp_milli_sec = time_stamp_micro_sec[:-3]

        rx_data_file_name = "rx_data_record_" + time_stamp_milli_sec
        dataset_filename = rx_data_file_name + ".sigmf-data"
        dataset_file_path = os.path.join(rx_args.rx_recorded_data_path, dataset_filename)
        print(dataset_file_path)
        rx_data.tofile(dataset_file_path)

        # Create sigmf metadata
        meta = SigMFFile(
            data_file=dataset_file_path,  # extension is optional
            global_info={
                SigMFFile.DATATYPE_KEY: "cf32_le",  # get_data_type_str(rx_data) - 'cf64_le' is not supported yet
                SigMFFile.SAMPLE_RATE_KEY: rx_args.coerced_rx_rate,  # args.rate,
                SigMFFile.NUM_CHANNELS_KEY: len(rx_args.channels),
                SigMFFile.AUTHOR_KEY: "Abdo Gaber",
                SigMFFile.DESCRIPTION_KEY: tx_args.waveform_file_name,
                SigMFFile.RECORDER_KEY: "UHD Python API",
                SigMFFile.LICENSE_KEY: "URL to the license document",
                SigMFFile.HW_KEY: "USRP " + rx_args.usrp_mboard_id,
                SigMFFile.DATASET_KEY: dataset_filename,
                SigMFFile.VERSION_KEY: sigmf.__version__,
            },
        )

        # Create a capture key at time index 0
        meta.add_capture(
            0,  # Sample Start
            metadata={
                SigMFFile.FREQUENCY_KEY: rx_args.coerced_rx_freq,  # args.freq,
                SigMFFile.DATETIME_KEY: dt.datetime.utcnow().isoformat() + "Z",
                "capture_details": {
                    "acquisition_bandwidth": rx_args.coerced_rx_bandwidth,
                    "gain": rx_args.coerced_rx_gain,
                    "attenuation": int(rx_args.channel_attenuation),  # args.channel_attenuation,
                    "source_file": os.path.basename(__file__),  # RF IQ recording filename that was used to create the file
                },
            },
        )

        # Get tx waveform config from file name
        tx_waveform_config = get_tx_waveform_config_info(tx_args.waveform_file_name)
        # Add an annotation
        meta.add_annotation(
            0,  # Sample Start
            rx_args.num_rx_samps,  # Sample count
            metadata={
                SigMFFile.FLO_KEY: rx_args.coerced_rx_freq
                - rx_args.coerced_rx_rate / 2,  # args.freq - args.rate / 2,
                SigMFFile.FHI_KEY: rx_args.coerced_rx_freq
                + rx_args.coerced_rx_rate / 2,  # args.freq + args.rate / 2,
                SigMFFile.LABEL_KEY: tx_waveform_config[0]+"_"+ tx_waveform_config[1],
                SigMFFile.COMMENT_KEY: "USRP RX IQ DATA CAPTURE",
                SigMFFile.GENERATOR_KEY: rx_args.usrp_serial_number,
                "signal:detail": {
                    "data_type": rx_data.dtype.name,
                    "system": "",
                    "standard": tx_waveform_config[0]+"_"+ tx_waveform_config[1],
                    "duplexing": tx_waveform_config[3],
                    "multiplexing": tx_waveform_config[9],
                    "multiple_access": tx_waveform_config[9],
                    "type": "digital",
                    "mod_class": tx_waveform_config[8],
                    "carrier_variant": tx_waveform_config[6],
                    "order": tx_waveform_config[8],
                    "bandwidth": tx_args.bandwidth,
                    #"channel": 78,  # channel number of the signal within the communication system.
                },
                "signal:emitter": {
                    "seid": tx_args.usrp_serial_number,  # Unique ID of the emitter
                    "manufacturer": "NI",
                    "power_tx": 8.0,
                },
            },
        )

        # Check for mistakes
        assert meta.validate()

        ## Write Meta Data to file
        dataset_meta_filename = rx_data_file_name + ".sigmf-meta"
        dataset_meta_file_path = os.path.join(rx_args.rx_recorded_data_path, dataset_meta_filename)
        meta.tofile(dataset_meta_file_path)  # extension is optional

        print(dataset_meta_file_path)
        print("")

# Get tx waveform config from file name 
# example: 
#         waveform name: ["NR_FR1_DL_FDD_SISO_BW-20MHz_CC-1_SCS-30kHz_Mod-64QAM_OFDM_TM3.1.tdms"]},
#         ['NR', 'FR1', 'DL', 'FDD', 'SISO', 'BW-20MHz', 'CC-1', 'SCS-30kHz', 'Mod-64QAM', 'OFDM']
# to do: Enhance the list to be as a dictonary
def get_tx_waveform_config_info(waveform_file_name):
    num_waveform_config_info = waveform_file_name.count("_")
    temp = waveform_file_name
    tx_waveform_config =[] 
    for i in range(num_waveform_config_info):
        tx_waveform_config.append(temp[0: temp.find("_")])
        temp = temp[temp.find("_")+1:] 
    
    return tx_waveform_config