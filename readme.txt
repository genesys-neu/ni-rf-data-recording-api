- Open terminal command:
- Go to the project directory
#----------------------------------------------
To run Replay test (only replay data) based on UHD Pytho API (TX only):
python3.9 rf_replay_data_transmitter_usrp_uhd.py  --args="type=x300,addr=192.168.40.2,master_clock_rate=184.32e6" --freq=2e9 --rate=30.72e6 --gain=30 --path="waveform-files/tdms/" --file="NR_FR1_DL_FDD_SISO_BW-20MHz_CC-1_SCS-30kHz_Mod-64QAM_OFDM_TM3.1" --waveform_format="tdms"
#----------------------------------------------
To run RF Data recorder based on UHD Pytho API (rx only):
python3.9 rf_data_recorder_usrp_uhd.py --nrecords 1 --args="type=x300,addr=192.168.40.2,master_clock_rate=184.32e6" --freq 2e9 --rate 30.72e6 --duration 10e-3 --channels 0 --gain 30 --rx_recorded_data_path /home/agaber/workarea/recorded-data
#----------------------------------------------
To main rf data recording api (TX + RX)
- First, change config parameters in JSON file: config_rf_data_recording_api.json
python3.9 main_rf_data_recording_api.py
