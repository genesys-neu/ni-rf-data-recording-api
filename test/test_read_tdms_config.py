## Read waveform data config from rfws file
# https://www.datacamp.com/community/tutorials/python-xml-elementtree

from pathlib import Path
from re import X
import xml.etree.cElementTree as ET

path="waveform-files/tdms/"
file="NR_FR1_DL_FDD_SISO_BW-20MHz_CC-1_SCS-30kHz_Mod-64QAM_OFDM_TM3.1"

def read_tdms_waveform_config (path,file):
    folder_path = (Path(__file__).parent /path).resolve()
    # the tdms waveform config file is saved with the same name of waveform but it has .rfws extenstion
    file_path = str(folder_path) + "/" + file + ".rfws"

    # change numerical string with k, M, or G to float number
    def freq_string_to_float(x):
        if "k" in x:
            x_str= x.replace("k", "000")
        elif "M" in x:
            x_str = x.replace("M", "000000")
        elif "G" in x:
            x_str = x.replace("G", "000000000")
        else:
            x_str = x
        return float(x_str)

    # reading the rfws file
    xmlDoc = ET.parse(file_path)
    root = xmlDoc.getroot()

    # XPath expressiion searching all elements recursively starting from root './/*'
    # that have an attribute 'name' with the value e.i. 'Bandwidth (Hz)'
    # returns a list, either iterate over the list or select list element zero [0] if you expect only one hit
    # more sophisticated expressions are possible
    waveform_config ={} 

    # get standard
    factory = root.findall(".//*[@name='factory']")
    factory = factory[0].text
    waveform_config["Standard"] = factory

    # get bandwidth
    bwElements = root.findall(".//*[@name='Bandwidth (Hz)']")
    bw = bwElements[0].text
    waveform_config["Bandwidth"] = freq_string_to_float(bw)

    # get freqeuncy range
    freqRanges = root.findall(".//*[@name='Frequency Range']")
    FR = freqRanges[0].text
    waveform_config["Freqeuncy_Range"] = FR

    # get link direction
    link_directions = root.findall(".//*[@name='Link Direction']")
    link_direction = link_directions[0].text 
    waveform_config["link_direction"] = link_direction

    # get number of frames
    n_frames_vec = root.findall(".//*[@name='Number of Frames']")
    n_frames = n_frames_vec[0].text
    waveform_config["n_frames"] = n_frames

    if waveform_config["link_direction"] == "Downlink":
        # check if test model is enabled
        dl_ch_config_modes = root.findall(".//*[@name='DL Ch Configuration Mode']")
        dl_ch_config_mode =  dl_ch_config_modes[0].text 
        if dl_ch_config_mode == "Test Model":
            # get DL test model
            dl_test_models = root.findall(".//*[@name='DL Test Model']")
            dl_test_model =  dl_test_models[0].text 
            waveform_config["dl_test_model"] = dl_test_model

            # get modulation type
            mod = root.findall(".//*[@name='DL Test Model Modulation Type']")
            # for PDSCH, select 
            mod =  mod[0].text
            waveform_config["MOD"] = mod    

            # get DL duplex
            dl_duplex = root.findall(".//*[@name='DL Test Model Duplex Scheme']")
            dl_duplex =  dl_duplex[0].text 
            waveform_config["dl_duplex"] = dl_duplex

        elif dl_ch_config_mode == "User Defined":
            # get DL test model
            waveform_config["dl_test_model"] = dl_ch_config_mode

            # get modulation type
            mod = root.findall(".//*[@name='Modulation Type']")
            # for PDSCH, select 
            mod =  mod[0].text
            waveform_config["MOD"] = mod  

            # get DL duplex
            waveform_config["dl_duplex"] = dl_ch_config_mode
    else:
        # get DL test model
        waveform_config["dl_test_model"] = "User Defined"
        
        # get modulation type
        mod = root.findall(".//*[@name='Modulation Type']")
        # for PUSCH, select 
        mod =  mod[1].text
        waveform_config["MOD"] = mod

        # get DL duplex
        waveform_config["dl_duplex"] = "User Defined"

    # get subcarrier spacing
    scs = root.findall(".//*[@name='Subcarrier Spacing (Hz)']")
    scs =  scs[0].text 
    waveform_config["SCS"] = freq_string_to_float(scs)

    # get CC index
    cc_index = root.findall(".//*[@name='CarrierCCIndex']")
    cc_index =  cc_index[0].text 
    waveform_config["CarrierCCIndex"] = cc_index

    # get ssb info
    ssb_config_set = root.findall(".//*[@name='Configuration Set']")
    ssb_config_set =  ssb_config_set[0].text 
    waveform_config["ssb_config_set"] = ssb_config_set

    # get ssb periodicity
    ssb_periodicity = root.findall(".//*[@name='Periodicity']")
    ssb_periodicity =  ssb_periodicity[0].text 
    waveform_config["ssb_periodicity"] = ssb_periodicity

    return waveform_config

waveform_config = read_tdms_waveform_config (path,file)
print(waveform_config)



