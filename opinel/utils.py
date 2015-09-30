# Import future print
from __future__ import print_function

# Opinel version
from opinel import __version__ as OPINEL_VERSION

# Import stock packages
import argparse
import copy
from collections import Counter
import datetime
from distutils import dir_util
from distutils.version import StrictVersion
import json
import fileinput
import os
import re
import shutil
import sys
from threading import Event, Thread
import traceback
# Python2 vs Python3
try:
    from Queue import Queue
except ImportError:
    from queue import Queue

# Import third-party packages
import boto3
import requests


########################################
# Globals
########################################

re_profile_name = re.compile(r'\[(.*)\]')
re_access_key = re.compile(r'aws_access_key_id')
re_secret_key = re.compile(r'aws_secret_access_key')
re_mfa_serial = re.compile(r'aws_mfa_serial')
re_session_token = re.compile(r'aws_session_token')
mfa_serial_format = r'^arn:aws:iam::\d+:mfa/[a-zA-Z0-9\+=,.@_-]+$'
re_mfa_serial_format = re.compile(mfa_serial_format)
re_gov_region = re.compile(r'(.*?)-gov-(.*?)')
re_cn_region = re.compile(r'^cn-(.*?)')

aws_credentials_file = os.path.join(os.path.join(os.path.expanduser('~'), '.aws'), 'credentials')
aws_credentials_file_tmp = os.path.join(os.path.join(os.path.expanduser('~'), '.aws'), 'credentials.tmp')


########################################
##### Argument parser
########################################

def init_parser():
    if not 'parser' in globals():
        global parser
        parser = argparse.ArgumentParser()

#
# Add a common argument to a recipe
#
def add_common_argument(parser, default_args, argument_name):
    if argument_name == 'debug':
        parser.add_argument('--debug',
                            dest='debug',
                            default=False,
                            action='store_true',
                            help='Print the stack trace when exception occurs')
    elif argument_name == 'dry-run':
        parser.add_argument('--dry-run',
                            dest='dry_run',
                            default=False,
                            action='store_true',
                            help='Executes read-only actions (check status, describe*, get*, list*...)')
    elif argument_name == 'profile':
        parser.add_argument('--profile',
                            dest='profile',
                            default= ['default'],
                            nargs='+',
                            help='Name of the profile')
    elif argument_name == 'regions':
        parser.add_argument('--regions',
                            dest='regions',
                            default=[],
                            nargs='+',
                            help='Name of regions to run the tool in, defaults to all')
    elif argument_name == 'with-gov':
        parser.add_argument('--with-gov',
                            dest='with_gov',
                            default=False,
                            action='store_true',
                            help='Include the Government regions')
    elif argument_name == 'with-cn':
        parser.add_argument('--with-cn',
                            dest='with_cn',
                            default=False,
                            action='store_true',
                            help='Include the China regions')
    elif argument_name == 'force':
        parser.add_argument('--force',
                            dest='force_write',
                            default=False,
                            action='store_true',
                            help='Overwrite existing files')
    else:
        raise Exception('Invalid parameter name %s' % argument_name)

init_parser()
add_common_argument(parser, {}, 'debug')
add_common_argument(parser, {}, 'profile')


########################################
##### Debug-related functions
########################################

def printException(e):
    global verbose_exceptions
    if verbose_exceptions:
        printError(str(traceback.format_exc()))
    else:
        printError(str(e))

def configPrintException(enable):
    global verbose_exceptions
    verbose_exceptions = enable


########################################
##### Output functions
########################################

def printError(msg, newLine = True):
    printGeneric(sys.stderr, msg, newLine)

def printInfo(msg, newLine = True ):
    printGeneric(sys.stdout, msg, newLine)

def printGeneric(out, msg, newLine = True):
    out.write(msg)
    if newLine == True:
        out.write('\n')
    out.flush()

########################################
##### File write functions
########################################

#
# Creates/Modifies file and saves python object as JSON
#
def save_blob_as_json(filename, blob, force_write, debug):
    try:
        if prompt_4_overwrite(filename, force_write):
            with open(filename, 'wt') as f:
                write_data_to_file(f, blob, force_write, debug)
    except Exception as e:
        printException(e)
        pass

#
# Dumps python object as JSON in opened file handler
#
def write_data_to_file(f, data, force_write, debug):
    print('%s' % json.dumps(data, indent = 4 if debug else None, separators=(',', ': '), sort_keys=True, cls=CustomJSONEncoder), file = f)

#
# JSON encoder class
#
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if type(o) == datetime.datetime:
            return str(o)
        else:
            return o.__dict__


########################################
# Common functions
########################################

#
# Build the list of target region names
#
def build_region_list(service, chosen_regions = [], include_gov = False, include_cn = False):
    boto_regions = []
    # h4ck pending botocore issue 339
    package_dir, foo = os.path.split(__file__)
    boto_endpoints_file = os.path.join(package_dir, 'data', 'boto-endpoints.json')
    with open(boto_endpoints_file, 'rt') as f:
        boto_endpoints = json.load(f)
        if not service in boto_endpoints:
            printError('Error: the service \'%s\' is not supported yet.' % service)
            return []
        for region in boto_endpoints[service]:
            boto_regions.append(region)
    if len(chosen_regions):
        return list((Counter(boto_regions) & Counter(chosen_regions)).elements())
    else:
        return [region for region in boto_regions if (not re_gov_region.match(region) or include_gov) and (not re_cn_region.match(region) or include_cn)]

#
# Check boto version
#
def check_boto3_version():
    printInfo('Checking the version of boto...')
    # TODO: read that from requirements file...
    min_boto3_version = '1.1.1'
    latest_boto3_version = 0
    if boto3.__version__ < min_boto3_version:
        printError('Error: the version of boto3 installed on this system (%s) is too old. Boto version %s or newer is required.' % (boto3.__version__, min_boto3_version))
        return False
    else:
        try:
            # Warn users who have not the latest version of boto installed
            release_tag_regex = re.compile('(\d+)\.(\d+)\.(\d+)')
            tags = requests.get('https://api.github.com/repos/boto/boto3/tags').json()
            for tag in tags:
                if release_tag_regex.match(tag['name']) and tag['name'] > latest_boto3_version:
                    latest_boto3_version = tag['name']
            if boto3.__version__ < latest_boto3_version:
                printError('Warning: the version of boto installed (%s) is not the latest available (%s). Consider upgrading to ensure that all features are enabled.' % (boto3.__version__, latest_boto3_version))
        except Exception as e:
            printError('Warning: connection to the Github API failed.')
            printException(e)
    return True

def check_opinel_version(min_version):
    if StrictVersion(OPINEL_VERSION) < StrictVersion(min_version):
        printError('Error: the version of opinel installed on this system(%s) is too old. You need at least version %s to run this tool.' % (OPINEL_VERSION, min_version))
        return False
    return True

#
# Connect to any service
#
def connect_service(service, key_id, secret, session_token, region_name = None, config = None, silent = False):
    try:
        client_params = {}
        client_params['service_name'] = service.lower()
        session_params = {}
        session_params['aws_access_key_id'] = key_id
        session_params['aws_secret_access_key'] = secret
        session_params['aws_session_token'] = session_token
        if region_name:
            client_params['region_name'] = region_name
            session_params['region_name'] = region_name
        if config:
            client_params['config'] = config
        aws_session = boto3.session.Session(**session_params)
        return aws_session.client(**client_params)
        if not silent:
            infoMessage = 'Connecting to AWS %s' % service
            if region_name:
                infoMessage = infoMessage + ' in %s' % region_name
            printInfo(infoMessage + '...')
    except Exception as e:
        printException(e)
        return None

#
# Return with priority: environment_name/profile_name/['default']
#
def get_environment_name(args):
    environment_name = ['default']
    if 'environment_name' in args and args.environment_name:
        environment_name = args.environment_name
    elif 'profile' in args and args.profile:
        environment_name = args.profile
    return environment_name

#
# Handle truncated responses
#
def handle_truncated_response(callback, params, marker_name, entities):
    results = {}
    for entity in entities:
        results[entity] = []
    while True:
        response = callback(**params)
        for entity in entities:
            results[entity] = results[entity] + response[entity]
        if marker_name in response and response[marker_name]:
            params[marker_name] = response[marker_name]
        else:
            break
    return results

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

def manage_dictionary(dictionary, key, init, callback=None):
    if not str(key) in dictionary:
        dictionary[str(key)] = init
        manage_dictionary(dictionary, key, init)
        if callback:
            callback(dictionary[key])
    return dictionary

def thread_work(targets, function, params = {}, num_threads = 0):
    # Init queue and threads
    q = Queue(maxsize=0)
    if not num_threads:
        num_threads = len(targets)
    for i in range(num_threads):
        worker = Thread(target=function, args=(q, params))
        worker.setDaemon(True)
        worker.start()
    for target in targets:
        q.put(target)
    q.join()

########################################
# Credentials read/write functions
########################################

#
# Fetch STS credentials
#
def init_sts_session(key_id, secret, mfa_serial = None, mfa_code = None):
    if not mfa_serial:
        # Prompt for MFA serial
        mfa_serial = prompt_4_mfa_serial()
        save_no_mfa_credentials = True
    if not mfa_code:
        # Prompt for MFA code
        mfa_code = prompt_4_mfa_code()
    # Fetch session token and set the duration to 8 hours
    sts_client = boto3.session.Session(key_id, secret).client('sts')
    sts_response = sts_client.get_session_token(SerialNumber = mfa_serial, TokenCode = mfa_code, DurationSeconds = 28800)
    return sts_response['Credentials']['AccessKeyId'], sts_response['Credentials']['SecretAccessKey'], sts_response['Credentials']['SessionToken']

#
# Read credentials from anywhere
#
def read_creds(profile_name, csv_file = None, mfa_serial_arg = None, mfa_code = None):
    key_id = None
    secret = None
    token = None
    if csv_file:
        key_id, secret, mfa_serial = read_creds_from_csv(csv_file)
    else:
        # Read from ~/.aws/credentials
        key_id, secret, mfa_serial, token = read_creds_from_aws_credentials_file(profile_name)
        if not key_id:
            # Read from EC2 instance metadata
            key_id, secret, token = read_creds_from_ec2_instance_metadata()
        if not key_id:
            # Read from environment variables
            key_id, secret, token = read_creds_from_environment_variables()
    # If an MFA serial was provided as an argument, discard whatever we found in config file
    if mfa_serial_arg:
        mfa_serial = mfa_serial_arg
    # If we don't have valid creds by now, throw an exception
    if key_id == None or secret == None:
        printError('Error: could not find AWS credentials. Use the --help option for more information.')
    return key_id, secret, token

#
# Read credentials from AWS config file
#
def read_creds_from_aws_credentials_file(profile_name, credentials_file = aws_credentials_file):
    key_id = None
    secret = None
    mfa_serial = None
    security_token = None
    try:
        with open(credentials_file, 'rt') as credentials:
            for line in credentials:
                profile_line = re_profile_name.match(line)
                if profile_line:
                    if profile_line.groups()[0] == profile_name:
                        profile_found = True
                    else:
                        profile_found = False
                if profile_found:
                    if re_access_key.match(line):
                        key_id = (line.split(' ')[2]).rstrip()
                    elif re_secret_key.match(line):
                        secret = (line.split(' ')[2]).rstrip()
                    elif re_mfa_serial.match(line):
                        mfa_serial = (line.split(' ')[2]).rstrip()
                    elif re_session_token.match(line):
                        security_token = (line.split(' ')[2]).rstrip()
    except Exception as e:
        pass
    return key_id, secret, mfa_serial, security_token

#
# Read credentials from a CSV file
#
def read_creds_from_csv(filename):
    key_id = None
    secret = None
    mfa_serial = None
    with open(filename, 'rt') as csvfile:
        for i, line in enumerate(csvfile):
            if i == 1:
                try:
                    username, key_id, secret = line.split(',')
                except:
                    try:
                        username, key_id, secret, mfa_serial = line.split(',')
                        mfa_serial = mfa_serial.rstrip()
                    except:
                        printError('Error, the CSV file is not properly formatted')
    return key_id.rstrip(), secret.rstrip(), mfa_serial

#
# Read credentials from EC2 instance metadata (IAM role)
#
def read_creds_from_ec2_instance_metadata():
    key_id = None
    secret = None
    token = None
    try:
        has_role = requests.get('http://169.254.169.254/latest/meta-data/iam/security-credentials')
        if has_role.status_code == 200:
            iam_role = has_role.text
            credentials = requests.get('http://169.254.169.254/latest/meta-data/iam/security-credentials/%s/' % iam_role.strip()).json()
            key_id = credentials['AccessKeyId']
            secret = credentials['SecretAccessKey']
            token = credentials['Token']
    except Exception as e:
        pass
    return key_id, secret, token

#
# Read credentials from environment variables
#
def read_creds_from_environment_variables():
    key_id = None
    secret = None
    session_token = None
    # Check environment variables
    if 'AWS_ACCESS_KEY_ID' in os.environ and 'AWS_SECRET_ACCESS_KEY' in os.environ:
        key_id = os.environ['AWS_ACCESS_KEY_ID']
        secret = os.environ['AWS_SECRET_ACCESS_KEY']
        if 'AWS_SESSION_TOKEN' in os.environ:
            session_token = os.environ['AWS_SESSION_TOKEN']
    return key_id, secret, session_token

#
# Read default argument values for a recipe
#
def read_profile_default_args(recipe_name):
    profile_name = 'default'
    # h4ck to have an early read of the profile name
    for i, arg in enumerate(sys.argv):
        if arg == '--profile' and len(sys.argv) >= i + 1:
            profile_name = sys.argv[i + 1]
    default_args = {}
    recipes_dir = os.path.join(os.path.join(os.path.expanduser('~'), '.aws'), 'recipes')
    recipe_file = os.path.join(recipes_dir, profile_name + '.json')
    if os.path.isfile(recipe_file):
        with open(recipe_file, 'rt') as f:
            config = json.load(f)
        t = re.compile(r'(.*)?\.py')
        for key in config:
            if not t.match(key):
                default_args[key] = config[key]
            elif key == parser.prog:
                default_args.update(config[key])
    return default_args

#
# Returns the argument default value, customized by the user or default programmed value
#
def set_profile_default(default_args, key, default):
    return default_args[key] if key in default_args else default

#
# Show profile names from ~/.aws/credentials
#
def show_profiles_from_aws_credentials_file():
    profiles = []
    files = [ aws_credentials_file ]
    for filename in files:
        if os.path.isfile(filename):
            with open(filename) as f:
                lines = f.readlines()
                for line in lines:
                    groups = re_profile_name.match(line)
                    if groups:
                        profiles.append(groups.groups()[0])
    for profile in set(profiles):
        printInfo(' * %s' % profile)

#
# Write credentials to AWS config file
#
def write_creds_to_aws_credentials_file(profile_name, key_id = None, secret = None, session_token = None, mfa_serial = None):
    profile_found = False
    profile_ever_found = False
    session_token_written = False
    mfa_serial_written = False
    # Create an empty file if target does not exist
    if not os.path.isfile(aws_credentials_file):
        open(aws_credentials_file, 'a').close()
    # Open and parse/edit file
    for line in fileinput.input(aws_credentials_file, inplace=True):
        profile_line = re_profile_name.match(line)
        if profile_line:
            if profile_line.groups()[0] == profile_name:
                profile_found = True
                profile_ever_found = True
            else:
                if profile_found:
                    if session_token and not session_token_written:
                        print('aws_session_token = %s' % session_token)
                        session_token_written = True
                    if mfa_serial and not mfa_serial_written:
                        print('aws_mfa_serial = %s' % mfa_serial)
                        mfa_serial_written = True
                profile_found = False
            print(line.rstrip())
        elif profile_found:
            if re_access_key.match(line) and key_id:
                print('aws_access_key_id = %s' % key_id)
            elif re_secret_key.match(line) and secret:
                print('aws_secret_access_key = %s' % secret)
            elif re_mfa_serial.match(line) and mfa_serial:
                print('aws_mfa_serial = %s' % mfa_serial)
                mfa_serial_written = True
            elif re_session_token.match(line) and session_token:
                print('aws_session_token = %s' % session_token)
                session_token_written = True
            else:
                print(line.rstrip())
        else:
            print(line.rstrip())

    # Complete the profile if needed
    if profile_found:
        with open(aws_credentials_file, 'a') as f:
            complete_profile(f, session_token, session_token_written, mfa_serial, mfa_serial_written)

    # Add new profile if not found
    if not profile_ever_found:
        with open(aws_credentials_file, 'a') as f:
            f.write('[%s]\n' % profile_name)
            f.write('aws_access_key_id = %s\n' % key_id)
            f.write('aws_secret_access_key = %s\n' % secret)
            complete_profile(f, session_token, session_token_written, mfa_serial, mfa_serial_written)

#
# Append session token and mfa serial if needed
#
def complete_profile(f, session_token, session_token_written, mfa_serial, mfa_serial_written):
    if session_token and not session_token_written:
        f.write('aws_session_token = %s\n' % session_token)
    if mfa_serial and not mfa_serial_written:
        f.write('aws_mfa_serial = %s\n' % mfa_serial)


########################################
##### Prompt functions
########################################

#
# Prompt for MFA code
#
def prompt_4_mfa_code(activate = False):
    while True:
        if activate:
            prompt_string = 'Enter the next value: '
        else:
            prompt_string = 'Enter your MFA code (or \'q\' to abort): '
        mfa_code = prompt_4_value(prompt_string, no_confirm = True)
        try:
            if mfa_code == 'q':
                return mfa_code
            int(mfa_code)
            mfa_code[5]
            break
        except:
            printError('Error, your MFA code must only consist of digits and be at least 6 characters long.')
    return mfa_code

#
# Prompt for MFA serial
#
def prompt_4_mfa_serial():
    while True:
        mfa_serial = prompt_4_value('Enter your MFA serial: ', required = False)
        if mfa_serial == '' or re_mfa_serial_format.match(mfa_serial):
            break
        else:
            printError('Error, your MFA serial must be of the form %s' % mfa_serial_format)
    return mfa_serial

#
# Prompt for file overwrite
#
def prompt_4_overwrite(filename, force_write):
    # Do not prompt if the file does not exist or force_write is set
    if not os.path.exists(filename) or force_write:
        return True
    return prompt_4_yes_no('File \'{}\' already exists. Do you want to overwrite it'.format(filename))

#
# Prompt for a value
#
def prompt_4_value(question, choices = None, default = None, display_choices = True, display_indices = False, authorize_list = False, is_question = False, no_confirm = False, required = True):
    if choices and len(choices) == 1 and choices[0] == 'yes_no':
        return prompt_4_yes_no(question)
    if choices and display_choices and not display_indices:
        question = question + ' (' + '/'.join(choices) + ')'
    while True:
        if choices and display_indices:
            for c in choices:
                printError('%3d. %s\n' % (choices.index(c), c))
        if is_question:
            question = question + '? '
        printError(question)
        try:
            choice = raw_input()
        except:
            choice = input()
        if choices:
            user_choices = [item.strip() for item in choice.split(',')]
            if not authorize_list and len(user_choices) > 1:
                printError('Multiple values are not supported; please enter a single value.')
            else:
                choice_valid = True
                if display_indices and int(choice) < len(choices):
                    choice = choices[int(choice)]
                else:
                    for c in user_choices:
                        if not c in choices:
                            printError('Invalid value (%s).' % c)
                            choice_valid = False
                            break
                if choice_valid:
                    return choice
        elif not choice and default:
            if prompt_4_yes_no('Use the default value (' + default + ')'):
                return default
        elif not choice and required:
            printError('You cannot leave this parameter empty.')
        elif no_confirm or prompt_4_yes_no('You entered "' + choice + '". Is that correct'):
            return choice

#
# Prompt for yes/no answer
#
def prompt_4_yes_no(question):
    while True:
        printError(question + ' (y/n)? ')
        try:
            choice = raw_input().lower()
        except:
            choice = input().lower()
        if choice == 'yes' or choice == 'y':
            return True
        elif choice == 'no' or choice == 'n':
            return False
        else:
            printError('\'%s\' is not a valid answer. Enter \'yes\'(y) or \'no\'(n).' % choice)
