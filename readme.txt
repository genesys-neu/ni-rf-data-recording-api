Open terminal command:
#----------------------------------------------
To run RF Data recorder based on UHD Pytho API:
python3.9 rf_data_recorder_usrp_uhd.py --nrecords 1 --args="type=x300,addr=192.168.40.2,master_clock_rate=184.32e6" --freq 2e9 --rate 30.72e6 --duration 10e-3 --channels 0 --gain 30 --output-file /home/agaber/workarea/recorded-data
#----------------------------------------------
To run Replay test (only replay data) based on UHD Pytho API:
python3.9 rf_replay_data_transmitter_usrp_uhd_test.py  --args="type=x300,addr=192.168.40.2,master_clock_rate=184.32e6" -p=0 -s=16000 -c=1 -k=2000
