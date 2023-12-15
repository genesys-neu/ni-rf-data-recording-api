#
# Copyright 2023 National Instruments Corporation
#
# SPDX-License-Identifier: MIT
#
"""
Run mmWave devices from TMYTek
"""
# Description:
#   Use for mmWave devices operate and related information get
#
import threading
from lib.data_format_conversion_lib import str2bool
try:
    from lib.TLKCoreService import TLKCoreService
    from lib.TMYPublic import DevInterface, RetCode, RFMode, UDState, BeamType, UDM_REF
except Exception as e:
    if e.msg.__contains__("No module named \'lib"):
        print("Please check if you have installed the TMYTek API.")
        input(" === There is no TMYTek API, do you want to continue? ===") # Just press the keyboard if no need to support mmWave
    else:
        raise Exception("ERROR: The TMYTek API can't work, please check pip install -r requirements.txt")


# Define the TLKCore service in singleton for TMYTek devices
class SingletonTLKCoreService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SingletonTLKCoreService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.TLKApi = TLKCoreService()
        self.device_list = self.scan_devices()

    # Scan TMYTek devices in the network
    def scan_devices(self):
        if self.TLKApi.running:
            ret = self.TLKApi.scanDevices()  # has to scan before getting the device name
            scan_list = ret.RetData  # change the return type to list
            if ret.RetCode is not RetCode.OK:
                if len(scan_list) == 0:
                    raise Exception("WARNING: No TMYTek devices found.")
                else:
                    input(" === There are some errors while scanning, do you want to continue? ===")
            else:
                return scan_list
        else:
            raise Exception("ERROR: The TMYTek API can't work.")


def start_ud_execution(config):
    service = SingletonTLKCoreService().TLKApi
    sn = config.serial_number
    if service.running:
        if service.initDev(sn).RetCode is not RetCode.OK:
            raise Exception("ERROR: The TMYTek device can't be initialized. SN: {}".format(sn))
        else:
            print("The TMYTek device is initialized successfully. SN:{}".format(sn))
            # set ud frequency
            lo_frequency = config.lo_frequency / 1000  # unit in kHz
            rf_frequency = config.rf_frequency / 1000  # unit in kHz
            if_frequency = config.if_frequency / 1000  # unit in kHz
            ud_bandwidth = config.bandwidth / 1000  # unit in kHz
            service.setUDFreq(sn, lo_frequency, rf_frequency, if_frequency, ud_bandwidth)

            # init channels
            disabled_channels = config.disabled_channels
            # enable all channels by default
            current_state = service.getUDState(sn)  # the state has to get before set
            service.setUDState(sn, 1, UDState.CH1)
            service.setUDState(sn, 1, UDState.CH2)
            # disable selected channels
            if disabled_channels:
                for index in disabled_channels:
                    if index == 1:
                        service.setUDState(sn, 0, UDState.CH1)  # channel1 is disabled
                    if index == 2:
                        service.setUDState(sn, 0, UDState.CH2)  # channel2 is disabled

            service.setUDState(sn, int(str2bool(config.enable_10MHz_clock_out)), UDState.OUT_10M)
            service.setUDState(sn, int(str2bool(config.enable_100MHz_clock_out)), UDState.OUT_100M)
            service.setUDState(sn, int(str2bool(config.enable_5V_out)), UDState.PWR_5V)
            service.setUDState(sn, int(str2bool(config.enable_9V_out)), UDState.PWR_9V)

            if config.clock_reference_100MHz == "internal":
                service.setUDState(sn, 0, UDState.SOURCE_100M)
            if config.clock_reference_100MHz == "external":
                service.setUDState(sn, 1, UDState.SOURCE_100M)
    else:
        raise Exception("ERROR: The TMYTek API can't work.")


def start_beamformer(config):
    service = SingletonTLKCoreService().TLKApi
    sn = config.serial_number
    if service.running:
        if service.initDev(sn).RetCode is not RetCode.OK:
            raise Exception("ERROR: The TMYTek device can't be initialized. SN: {}".format(sn))
        else:
            print("The TMYTek device is initialized successfully. SN:{}".format(sn))
            if config.rf_mode == "Tx":
                mode = RFMode.TX
            if config.rf_mode == "Rx":
                mode = RFMode.RX
            service.setRFMode(sn, mode)
            # Set operating frequency
            operating_frequency = round(config.rf_frequency / 10 ** 9, 1)
            ret = service.setOperatingFreq(sn, operating_frequency)  # unit in Ghz: e.g 28.0
            if ret.RetCode is not RetCode.OK:
                raise Exception("ERROR: Can't set the operating frequency as {}.".format(operating_frequency))
            # Select the AAKit according to the table in the 'file' folder
            aakit_list = service.getAAKitList(sn).RetData
            for aaKit in aakit_list:
                if aaKit in config.antenna_array_specification_table:
                    service.selectAAKit(sn, config.antenna_array_specification_table)
                    break
                else:
                    raise Exception("ERROR: Can't find aakit in {}.".format(config.antenna_array_specification_table))
            # Get channel number
            channel_disable_settings = service.getChannelSwitch(sn, mode).RetData  # 2D array
            channel_num = len(channel_disable_settings) * len(channel_disable_settings[0])
            # Enable all channels by default
            for i in range(1, channel_num + 1):
                service.switchChannel(sn, i, False)
            # Disable specific channels according to config
            if config.disabled_antenna_elements:
                for n in config.disabled_antenna_elements:
                    service.switchChannel(sn, n, True)

            # Beam steering
            if config.beamformer_config_mode == "per_antenna_element":
                # Set gain and phase by channels
                gain_phase_pair = zip(config.antenna_element_gain_list, config.antenna_element_phase_list_deg)
                for index, (gain, phase) in enumerate(gain_phase_pair):
                    channel_index = index + 1
                    service.setChannelGainPhase(sn, channel_index, gain, phase)
            if config.beamformer_config_mode == "target_beam_properties":
                # Set beam pattern
                service.setBeamAngle(sn, config.beam_gain_db, config.beam_angle_elevation_deg,
                                     config.beam_angle_azimuth_deg)
    else:
        raise Exception("ERROR: The TMYTek API can't work.")


def deinit_mmwave_device(serial_number):
    service = SingletonTLKCoreService().TLKApi
    if service.running:
        if service.initDev(serial_number).RetCode is RetCode.OK:
            service.DeInitDev(serial_number)
            print("The TMYTek device is deinit. SN: {}".format(serial_number))


def get_device_name(serial_number):
    service = SingletonTLKCoreService().TLKApi
    if service.initDev(serial_number).RetCode is not RetCode.OK:
        raise Exception(
            "ERROR: The TMYTek device can't be initialized. SN: {}".format(serial_number))
    else:
        device_name = service.getDevTypeName(serial_number)
        return device_name


def get_device_type(serial_number):
    device_type = None
    device_name = get_device_name(serial_number)
    scan_result = SingletonTLKCoreService().device_list  # ["SN1, IP1, Device_Type1", "SN2, IP2, Device_Type2",...]
    matching_devices = [device_info for device_info in scan_result if serial_number in device_info]
    if matching_devices:
        matching_device = matching_devices[0]
        sn, ip, device_type = matching_device.split(",")
        device_type = device_type.strip()
    if device_type != '':
        device_type = device_name + ":" + device_type  # eg. BBox One:9
        print(f"Find the device type of SN {serial_number} ：{device_type}")
    else:
        print(f"Can't find the device type of SN {serial_number}")
    return device_type
