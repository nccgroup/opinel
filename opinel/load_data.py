# Import stock packages
import json
import os

#
# Load data from json file
#
def load_data(data_file, key_name = None, local_file = False):
    if local_file:
        src_dir = os.getcwd()
    else:
        src_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
    with open(os.path.join(src_dir, data_file)) as f:
        data = json.load(f)
    if key_name:
        data = data[key_name]
    return data
