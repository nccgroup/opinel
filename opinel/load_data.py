# Import stock packages
import json
import os

#
# Load data from json file
#
def load_data(data_file, key_name = None, local_file = False):
    if local_file:
        if data_file.startswith('/'):
            src_file = data_file
        else:
            src_dir = os.getcwd()
            src_file = os.path.join(src_dir, data_file)
    else:
        src_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
        src_file = os.path.join(src_dir, data_file)
    with open(src_file) as f:
        data = json.load(f)
    if key_name:
        data = data[key_name]
    return data
