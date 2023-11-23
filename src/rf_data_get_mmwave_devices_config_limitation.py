#
# Copyright 2023 National Instruments Corporation
#
# SPDX-License-Identifier: MIT
#
"""
 RF Data Get mmWave Device Configuration Limitation API
"""
from lib.TMYPublic import RetCode
from lib.run_mmWave_device import SingletonTLKCoreService, get_device_name

# Description:
#   Used to facilitate the user to know valid frequency and gain limitation value for all BBox in the network
#   as the reference before editing the configure file
#
if __name__ == "__main__":
    # print frequency list and gain limitation value for all BBox in the network
    service = SingletonTLKCoreService().TLKApi
    scan_list = SingletonTLKCoreService().device_list
    device_list = []
    for device in scan_list:
        device_dict = {}
        sn, ip, device_type = device.split(",")
        serial_number = sn.strip()
        device_name = get_device_name(serial_number)
        if device_name.startswith("BBox"):
            if service.running:
                if service.initDev(serial_number).RetCode is not RetCode.OK:
                    raise Exception("ERROR: The TMYTek device can't be initialized. SN: {}".format(sn))
                else:
                    device_dict["serial_number"] = serial_number
                    freq_list = service.getFrequencyList(serial_number).RetData
                    device_dict["freq_list"] = freq_list
                    for frequency in freq_list:
                        dr_dict = {}
                        service.setOperatingFreq(sn, frequency)  # getDR() relies on the calibration table of BBox series
                        dynamic_range_dict = service.getDR(serial_number).RetData
                        dr_dict["TX_MIN_GAIN"] = dynamic_range_dict["TX"][0]
                        dr_dict["TX_MAX_GAIN"] = dynamic_range_dict["TX"][1]
                        dr_dict["RX_MIN_GAIN"] = dynamic_range_dict["RX"][0]
                        dr_dict["RX_MAX_GAIN"] = dynamic_range_dict["RX"][1]
                        device_dict[str(frequency)] = dr_dict
                    device_list.append(device_dict)
        else:
            continue
    print(device_list)
