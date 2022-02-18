import sigmf

handle = sigmf.sigmffile.fromfile("recorded-data/rx_data_0.sigmf")
print(handle.read_samples())  # returns all timeseries data
handle.get_global_info()  # returns 'global' dictionary
print(handle.get_global_info)
handle.get_captures()  # returns list of 'captures' dictionaries
print(handle.get_captures)
handle.get_annotations()  # returns list of all annotations
print(handle.get_annotations)
