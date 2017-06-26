# -*- coding: utf-8 -*-
from __future__ import print_function

import datetime
import json
import os
import re
import sys

from opinel.utils.console import printException, prompt_4_overwrite
from opinel.utils.conditions import pass_condition



class CustomJSONEncoder(json.JSONEncoder):
    """
    JSON encoder class
    """
    def default(self, o):
        if type(o) == datetime.datetime:
            return str(o)
        else:
            return o.__dict__


def load_data(data_file, key_name = None, local_file = False):
    """
    Load a JSON data file

    :param data_file:
    :param key_name:
    :param local_file:
    :return:
    """
    if local_file:
        if data_file.startswith('/'):
            src_file = data_file
        else:
            src_dir = os.getcwd()
            src_file = os.path.join(src_dir, data_file)
    else:
        src_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data')
        src_file = os.path.join(src_dir, data_file)
    with open(src_file) as f:
        data = json.load(f)
    if key_name:
        data = data[key_name]
    return data


def read_ip_ranges(filename, local_file = True, conditions = [], ip_only = False):
    """
    Returns the list of IP prefixes from an ip-ranges file

    :param filename:
    :param local_file:
    :param conditions:
    :param ip_only:
    :return:
    """
    targets = []
    data = load_data(filename, 'prefixes', local_file)
    for d in data:
        condition_passed = True
        for condition in conditions:
            condition_passed = pass_condition(d[condition[0]], condition[1], condition[2])
            if not condition_passed:
                break
        if condition_passed:
            targets.append(d)
    if ip_only:
        ips = []
        for t in targets:
            ips.append(t['ip_prefix'])
        return ips
    else:
        return targets


def save_blob_as_json(filename, blob, force_write, debug):
    """
    Creates/Modifies file and saves python object as JSON

    :param filename:
    :param blob:
    :param force_write:
    :param debug:

    :return:
    """
    try:
        if prompt_4_overwrite(filename, force_write):
            with open(filename, 'wt') as f:
                print('%s' % json.dumps(blob, indent=4 if debug else None, separators=(',', ': '), sort_keys=True, cls=CustomJSONEncoder), file=f)
    except Exception as e:
        printException(e)
        pass


def save_ip_ranges(profile_name, prefixes, force_write, debug):
    """
    Creates/Modifies an ip-range-XXX.json file

    :param profile_name:
    :param prefixes:
    :param force_write:
    :param debug:

    :return:
    """
    filename = 'ip-ranges-%s.json' % profile_name
    ip_ranges = {}
    ip_ranges['createDate'] = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    ip_ranges['prefixes'] = prefixes
    save_blob_as_json(filename, ip_ranges, force_write, debug)
