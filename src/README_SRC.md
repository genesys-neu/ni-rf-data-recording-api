# Source Code
It has the source code. This folder has the following items:
- Main functions (Python scripts) to execute the API.
- **Waveforms** folder: It has several waveforms collected based on the related wireless standard in four subfolders for 5G NR, LTE, Radar, and WiFi. New Waveforms go here.
- **Config** folder: It has the configuration files in JSON and YAML format. New configuration files go here.
- **lib** folder: It has the components of API library. New functions related to API lib go here.
- **tests** folder: It has some testbench for different purposes such as the following:
    - test_read_tdms_file_properties.py
    - test_read_tdms_file_spectrogram.py: Read Tx Waveform and plot its spectrogram.
    - test_rf_data_recording_config_interface: It reads the configuration file in YAML or JSON format and creates the variation map by doing a cross product over all possible values.
    - test_read_waveform_config_interface.py
    - test_read_waveform_data_interface.py
    - test_read_sigmf_meta_data_file
    - ... New testbenches go here.