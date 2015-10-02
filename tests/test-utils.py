
# Import AWS utils
from opinel.utils import *

# Import stock packages
import argparse
import json
import os
import shutil

#
# Test methods from utils.py
#
class TestUtilsClass:

    #
    # Unit tests for build_region_list()
    #
    def test_build_region_list(self):
        assert type(build_region_list('ec2', [])) == list
        assert type(build_region_list('ec2', [], True, True)) == list
        assert 'cn-north-1' in build_region_list('ec2', [], False, True)
        assert 'cn-north-1' not in build_region_list('ec2', [], False, False)
        assert 'us-gov-west-1' in build_region_list('ec2', [], True, False)
        assert 'us-gov-west-1' not in build_region_list('ec2', [], False, False)
        assert build_region_list('', True, True) == []

    #
    # Unit tests for get_environment_name()
    #
    def test_get_environment_name(self):
        # No profile and no environment name : returns a one-item list with 'default'
        args = argparse.Namespace()
        assert get_environment_name(args) == ['default']
        # Profile and no environment name : profile
        args.profile = ['profile']
        assert get_environment_name(args) == ['profile']
        args.profile = ['a', 'b', 'c']
        assert get_environment_name(args) == ['a', 'b', 'c']
        # Environment name has priority
        args.environment_name = ['env']
        assert get_environment_name(args) == ['env']
        args.environment_name = ['d', 'e', 'f']
        assert get_environment_name(args) ==  ['d', 'e', 'f']

    #
    #
    #
#def handle_truncated_responses(callback, callback_args, items_name):


    #
    #
    #
    def test_manage_dictionary(self):
    # def manage_dictionary(dictionary, key, init, callback=None):
        test = {}
        manage_dictionary(test, 'a', [])
        assert 'a' in test
        manage_dictionary(test, 'a', {})
        assert test['a'] == []
        # TODO: add callback test case

    #
    # Unit tests for load_data()
    #
    def test_load_data(self):
        test = load_data('protocols.json', 'protocols')
        assert type(test) == dict
        assert test['1'] == 'ICMP'
        test = load_data('tests/data/protocols.json', 'protocols', True)
        assert type(test) == dict
        assert test['-2'] == 'TEST'
        # TODO : add test case without key name (both local and not local)

    #
    # Unit tests for read_ip_ranges()
    #
    def test_read_ip_ranges(self):
        successful_read_ip_ranges_runs = True
        test_cases = [
                # Read from local file, no conditions, all data
                {
                    'filename': 'tests/data/ip-ranges-1.json',
                    'local_file': True,
                    'conditions': [],
                    'ip_only': False,
                    'results': 'tests/results/read_ip_ranges/ip-ranges-1a.json'
                },
                # Read from local file, no conditions, IPs only
                {
                    'filename': 'tests/data/ip-ranges-1.json',
                    'local_file': True,
                    'conditions': [],
                    'ip_only': True,
                    'results': 'tests/results/read_ip_ranges/ip-ranges-1b.json'
                },
                # Read from local file, with conditions, IPs only
                {
                    'filename': 'tests/data/ip-ranges-1.json',
                    'local_file': True,
                    'conditions': [["field_a", "equal", "a1"]],
                    'ip_only': True,
                    'results': 'tests/results/read_ip_ranges/ip-ranges-1c.json'
                },
                # Read from global file, with conditions
                {
                    'filename': 'ip-ranges.json',
                    'local_file': False,
                    'conditions': [["ip_prefix", "equal", "23.20.0.0/14"]],
                    'ip_only': False,
                    'results': 'tests/results/read_ip_ranges/ip-ranges-a.json'
                }
        ]
        for test_case in test_cases:
            results = test_case.pop('results')
            test_results = read_ip_ranges(**test_case)
            known_results = load_data(results, local_file = True)
            if cmp(test_results, known_results) != 0:
                successful_read_ip_ranges_runs = False
        assert(successful_read_ip_ranges_runs)

    #
    # Unit tests for save_ip_ranges()
    #
#    def test_save_ip_ranges(self):
#    save_ip_ranges(profile_name, prefixes, force_write, debug):

#def init_parser():
#def add_common_argument(parser, default_args, argument_name):
#def printException(e):
#def configPrintException(enable):
#def printError(msg, newLine = True):
#def printInfo(msg, newLine = True ):
#def printGeneric(out, msg, newLine = True):
#def check_boto3_version():
#def connect_service(service, key_id, secret, session_token, region_name = None, config = None, silent = False):
#def handle_truncated_responses(callback, callback_args, items_name):
#def thread_work(connection_info, service_info, targets, function, display_function = None, service_params = {}, num_threads = 0):
#def init_sts_session(key_id, secret, mfa_serial = None, mfa_code = None):
#def read_creds(profile_name, csv_file = None, mfa_serial_arg = None, mfa_code = None):
#def read_creds_from_aws_credentials_file(profile_name, credentials_file = aws_credentials_file):
#def read_creds_from_csv(filename):
#def read_creds_from_ec2_instance_metadata():
#def read_creds_from_environment_variables():
#def read_profile_default_args(recipe_name):
#def set_profile_default(default_args, key, default):
#def show_profiles_from_aws_credentials_file():
#def write_creds_to_aws_credentials_file(profile_name, key_id = None, secret = None, session_token = None, mfa_serial = None):
#def complete_profile(f, session_token, session_token_written, mfa_serial, mfa_serial_written):
#def prompt_4_mfa_code(activate = False):
#def prompt_4_mfa_serial():
#def prompt_4_value(question, choices = None, default = None, display_choices = True, display_indices = False, authorize_list = False, is_question = False, no_confirm = False, required = True):
#def prompt_4_yes_no(question):

