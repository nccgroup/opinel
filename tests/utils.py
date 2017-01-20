
# Import AWS utils
from opinel.utils import *

# Import stock packages
import argparse
import datetime
import json
import os
import shutil

#
# Test methods from utils.py
#
class TestUtilsClass:

    #
    # Implement cmp() for tests in Python3
    #
    def cmp(self, a, b):
        return (a > b) - (a < b)
    
    #
    # init_parser() is called when importing opinel.utils
    #
    def test_init_parser(self):
        assert 'parser' in globals()
        assert type(globals()['parser']) == argparse.ArgumentParser 

    #
    # Unit tests for add_common_argument()
    #
    def add_common_argument(self): # parser, default_args, argument_name):
        global parser
        add_common_argument(parser, None, 'dry-run')
        add_common_argument(parser, None, 'regions')
        add_common_argument(parser, None, 'partition-name')
        add_common_argument(parser, None, 'vpc')
        add_common_argument(parser, None, 'force')
        add_common_argument(parser, None, 'ip-ranges')
        add_common_argument(parser, None, 'ip-ranges-key-name')


    #
    # Unit tests for print functions
    #
#    def test_print_functions(self):
#        e = Exception()
#        configPrintException(True)
#        printException(e)
#        configPrintException(False)
#        printException(e)
#        printError('Error', False)
#        printError('Error', True)
#        printInfo('Info', False)
#        printInfo('Info', True)
#        printGeneric(sys.stdout, 'Generic', False)
#        printGeneric(sys.stderr, 'Generic', True)

    #
    # Unit tests for check_bot_version()
    #
    def test_check_boto3_version(self):
        assert check_boto3_version() == True
        assert check_boto3_version('42') == False



#def handle_truncated_responses(callback, callback_args, items_name):
#def thread_work(connection_info, service_info, targets, function, display_function = None, service_params = {}, num_threads = 0):
#def read_creds(profile_name, csv_file = None, mfa_serial_arg = None, mfa_code = None):



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
            if self.cmp(test_results, known_results) != 0:
                successful_read_ip_ranges_runs = False
        assert(successful_read_ip_ranges_runs)



#def save_blob_as_json(filename, blob, force_write, debug):
#def save_ip_ranges(profile_name, prefixes, force_write, debug):
#def write_data_to_file(f, data, force_write, debug):
#    def default(self, o):

    #
    # Unit tests for build_region_list()
    #
    def test_build_region_list(self):
        assert type(build_region_list('ec2', [])) == list
        assert type(build_region_list('ec2', [], 'aws-us-gov')) == list
        assert 'cn-north-1' in build_region_list('ec2', [], 'aws-cn')
        assert 'cn-north-1' not in build_region_list('ec2')
        assert 'us-gov-west-1' in build_region_list('ec2', [], 'aws-us-gov')
        assert 'us-gov-west-1' not in build_region_list('ec2')
        assert ['us-east-1'] == build_region_list('ec2', ['us-east-1'])
        assert 'us-west-2' in build_region_list('ec2', ['us-east-1', 'us-east-2', 'us-west-2'])
        assert 'us-east-1' not in build_region_list('ec2', ['us-west-1'])
        assert 'us-east-1' not in build_region_list('ec2', ['us-east-1', 'us-east-2'], 'aws-cn')
        assert build_region_list('') == []


#def check_boto3_version():
#def check_opinel_version(min_version, max_version = None):
#def get_opinel_requirement():


    #
    # Unit tests for connect_service()
    #
    def test_connect_service(self): # service, credentials, region_name = None, config = None, silent = False):
        creds = read_creds('default')
        c1 = connect_service('iam', creds)
        c2 = connect_service('ec2', creds, 'us-east-1')
        

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
    # Unit tests for manage_dictionary()
    #
    def test_manage_dictionary(self):
    # def manage_dictionary(dictionary, key, init, callback=None):
        test = {}
        manage_dictionary(test, 'a', [])
        assert 'a' in test
        manage_dictionary(test, 'a', {})
        assert test['a'] == []
        # TODO: add callback test case


#def thread_work(targets, function, params = {}, num_threads = 0):
#def threaded_per_region(q, params):
#def assume_role(role_name, credentials, role_arn, role_session_name):
#def get_cached_credentials_filename(role_name, role_arn):

    #
    # Unit tests for init_creds()
    #
    def test_init_creds(self):
        creds = init_creds()
        assert(type(creds)) == dict
        assert 'AccessKeyId' in creds
        assert 'SecretAccessKey' in creds
        assert 'Expiration' in creds
        assert 'SerialNumber' in creds
        assert 'TokenCode' in creds


    #
    # Unit tests for init_sts_session()
    #
    #def init_sts_session(profile_name, credentials, duration = 28800, session_name = None, write_to_file = True):
    def test_init_sts_session(self):
        creds = read_creds('default')
        creds = init_sts_session('default', creds, write_to_file = False)
        current = datetime.datetime.utcnow()
        assert creds['Expiration'].replace(tzinfo=None) > current
        creds = read_creds('default')
        creds = init_sts_session('default', creds, duration = 900, write_to_file = False)
        future = current + datetime.timedelta(hours=1)
        assert creds['Expiration'].replace(tzinfo=None) > current
        assert creds['Expiration'].replace(tzinfo=None) < future


    #
    # Unit tests for read_creds()
    #
    #def read_creds(profile_name, csv_file = None, mfa_serial_arg = None, mfa_code = None, force_init = False, role_session_name = 'opinel'):
    #def test_read_creds(self):
        

    #
    # Unit tests for read_creds_from_aws_credentials_file()
    #
    def test_read_creds_from_aws_credentials_file(self):
        test_cases = [
            {'profile_name': 'l01cd3v-1', 'credentials_file': 'tests/data/credentials'},
            {'profile_name': 'l01cd3v-2', 'credentials_file': 'tests/data/credentials'},
            {'profile_name': 'l01cd3v-3', 'credentials_file': 'tests/data/credentials'},
            {'profile_name': 'l01cd3v-4', 'credentials_file': 'tests/data/credentials'}
        ]
        results = [
            ('AKIAXXXXXXXXXXXXXXX1', 'deadbeefdeadbeefdeadbeefdeadbeef11111111', 'arn:aws:iam::123456789111:mfa/l01cd3v', None),
            ('AKIAXXXXXXXXXXXXXXX2', 'deadbeefdeadbeefdeadbeefdeadbeef22222222', 'arn:aws:iam::123456789222:mfa/l01cd3v', None),
            ('ASIAXXXXXXXXXXXXXXX3', 'deadbeefdeadbeefdeadbeefdeadbeef33333333', None, 'deadbeef333//////////ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg==/ZGVhZGJlZWZkZWFkYmVlZg==+ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg==/ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg=='),
            ('ASIAXXXXXXXXXXXXXXX4', 'deadbeefdeadbeefdeadbeefdeadbeef44444444', None, 'deadbeef444//////////ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg==/ZGVhZGJlZWZkZWFkYmVlZg==+ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg==/ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg==')
        ]
        for test_case, result in zip(test_cases, results):
            credentials = read_creds_from_aws_credentials_file(**test_case)
            assert(credentials['AccessKeyId'] == result[0])
            assert(credentials['SecretAccessKey'] == result[1])
            assert(credentials['SerialNumber'] == result[2])
            assert(credentials['SessionToken'] == result[3])


    #
    # Unit testsfor read_creds_from_csv()
    #
    def test_read_creds_from_csv(self):
        key, sec, mfa = read_creds_from_csv('tests/data/credentials1.csv')
        assert key == 'AKIAAAAAAAAAAAAAAAAA'
        assert sec == 'dddddddddddddddddddddddddddddddddddddddd'
        assert mfa == None
        key, sec, mfa = read_creds_from_csv('tests/data/credentials2.csv')
        assert key == 'AKIAAAAAAAAAAAAAAAAA'
        assert sec == 'dddddddddddddddddddddddddddddddddddddddd'
        assert mfa == 'arn:aws:iam::123456789012:mfa/username'


    #
    # Automatically called when running tests in Travis ?
    #
    def test_read_creds_from_ec2_instance_metadata(self):
        printInfo('Success ?')


    #
    # Unit tests for read_creds_from_environment_variables()
    #
#    def test_read_creds_from_environment_variables(self):
#        if 'AWS_ACCESS_KEY_ID' not in os.environ:
#            os.environ['AWS_ACCESS_KEY_ID'] = 'AKIAAAAAAAAAAAAAAAAA'
#        key, sec, mfa = read_creds_from_environment_variables()
#        assert key.startswith('AKIA') or key.startswith('ASIA')
#        assert mfa == None


    #def read_profile_default_args(recipe_name):
    #def read_profile_from_aws_config_file(profile_name, config_file = aws_config_file):
    #def set_profile_default(default_args, key, default):
    #def show_profiles_from_aws_credentials_file():
    #def write_creds_to_aws_credentials_file(profile_name, credentials):
    #def complete_profile(f, session_token, session_token_written, mfa_serial, mfa_serial_written):

    #
    # No unit tests for prompt functions
    # 
    # def test_prompt_functions(self):

    #
    # Unit test for pass_condition()
    # 
    #def pass_condition(b, test, a):
