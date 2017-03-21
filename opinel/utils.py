# Import future print
from __future__ import print_function

# Opinel version
from opinel import __version__ as OPINEL_VERSION
from opinel.load_data import load_data
from iampoliciesgonewild import get_actions_from_statement

# Import stock packages
import argparse
import copy
from collections import Counter
import datetime
import dateutil.parser
from distutils import dir_util
from distutils.version import StrictVersion
import json
import fileinput
import netaddr
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
from botocore.session import Session
import boto3
import requests


########################################
# Globals
########################################

verbose_exceptions = False

re_profile_name = re.compile(r'\[(.*)\]')
re_access_key = re.compile(r'aws_access_key_id')
re_secret_key = re.compile(r'aws_secret_access_key')
re_mfa_serial = re.compile(r'aws_mfa_serial')
re_role_arn = re.compile(r'role_arn')
re_session_token = re.compile(r'aws_session_token')
re_security_token = re.compile(r'aws_security_token')
re_expiration = re.compile(r'expiration')
re_source_profile = re.compile(r'source_profile')
mfa_serial_format = r'^arn:aws:iam::\d+:mfa/[a-zA-Z0-9\+=,.@_-]+$'
re_mfa_serial_format = re.compile(mfa_serial_format)
re_gov_region = re.compile(r'(.*?)-gov-(.*?)')
re_cn_region = re.compile(r'^cn-(.*?)')
re_opinel = re.compile(r'^opinel>=([0-9.]+),<([0-9.]+).*')
re_port_range = re.compile(r'(\d+)\-(\d+)')
re_single_port = re.compile(r'(\d+)')

aws_config_dir = os.path.join(os.path.expanduser('~'), '.aws')
aws_credentials_file = os.path.join(aws_config_dir, 'credentials')
aws_credentials_file_tmp = os.path.join(aws_config_dir, 'credentials.tmp')
aws_config_file = os.path.join(aws_config_dir, 'config')

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
    elif argument_name == 'partition-name':
        parser.add_argument('--partition-name',
                            dest='partition_name',
                            default='aws',
                            help='Switch out of the public AWS partition (e.g. US gov or China)')
    elif argument_name == 'vpc':
        parser.add_argument('--vpc',
                            dest='vpc',
                            default=[],
                            nargs='+',
                            help='Name of VPC to run the tool in, defaults to all')

    elif argument_name == 'force':
        parser.add_argument('--force',
                            dest='force_write',
                            default=False,
                            action='store_true',
                            help='Overwrite existing files')
    elif argument_name == 'ip-ranges':
        parser.add_argument('--ip-ranges',
                            dest='ip_ranges',
                            default=[],
                            nargs='+',
                            help='Config file(s) that contain your known IP ranges.')
    elif argument_name == 'ip-ranges-key-name':
        parser.add_argument('--ip-ranges-key-name',
                            dest='ip_ranges_key_name',
                            default='name',
                            help='Name of the key containing the display name of a known CIDR.')
    else:
        raise Exception('Invalid parameter name %s' % argument_name)

#
# Add an STS-related argument to a recipe
#
def add_sts_argument(parser, argument_name):
    if argument_name == 'mfa-serial':
        parser.add_argument('--mfa-serial',
                            dest='mfa_serial',
                            default=None,
                            help='MFA device\'s serial number')
    elif argument_name == 'mfa-code':
        parser.add_argument('--mfa-code',
                            dest='mfa_code',
                            default=None,
                            help='MFA code')
    elif argument_name == 'external-id':
        parser.add_argument('--external-id',
                            dest='external_id',
                            default=None,
                            help='External ID')
    elif argument_name == 'role-arn':
        parser.add_argument('--role-arn',
                            dest='role_arn',
                            default=None,
                            help='Role to be assumed.')
    elif argument_name == 'source-profile':
        parser.add_argument('--source-profile',
                            dest='source_profile',
                            default=None,
                            help='Profile to use when assuming role.')
    else:
        raise Exception('Invalid parameter name: %s' % argument_name)

init_parser()
add_common_argument(parser, {}, 'debug')
add_common_argument(parser, {}, 'profile')


########################################
##### Debug-related functions
########################################

def printException(e):
    global verbose_exceptions
    if verbose_exceptions:
        try:
            printError(str(traceback.format_exc()))
        except:
            printError(str(e))
    else:
        printError(str(e))

def configPrintException(enable):
    global verbose_exceptions
    verbose_exceptions = enable


########################################
##### Output functions
########################################

def printDebug(msg):
    if 'verbose_exceptions' not in globals():
        return
    global verbose_excpetions
    if verbose_exceptions:
        printGeneric(sys.stdout, msg)

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
##### File read/write functions
########################################

#
# Returns the list of IP prefixes from an ip-ranges file
#
def read_ip_ranges(filename, local_file = True, conditions = [], ip_only = False):
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
# Creates/Modifies an ip-range.json file
#
def save_ip_ranges(profile_name, prefixes, force_write, debug):
    filename = 'ip-ranges-%s.json' % profile_name
    ip_ranges = {}
    ip_ranges['createDate'] = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    ip_ranges['prefixes'] = prefixes
    save_blob_as_json(filename, ip_ranges, force_write, debug)

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
def build_region_list(service, chosen_regions = [], partition_name = 'aws'):
    # Of course things aren't that easy...
    service = 'ec2containerservice' if service == 'ecs' else service
    # Get list of regions from botocore
    regions = Session().get_available_regions(service, partition_name = partition_name)
    if len(chosen_regions):
        return list((Counter(regions) & Counter(chosen_regions)).elements())
    else:
        return regions

#
# Check boto version
#
def check_boto3_version(min_boto3_version = None):
    printInfo('Checking the version of boto...')
    if not min_boto3_version:
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

def check_opinel_version(min_version, max_version = None):
    if StrictVersion(OPINEL_VERSION) < StrictVersion(min_version):
        printError('Error: the version of opinel installed on this system(%s) is too old. You need at least version %s to run this tool.' % (OPINEL_VERSION, min_version))
        return False
    return True

def get_opinel_requirement():
    requirements_file = os.path.join(os.getcwd(), 'requirements.txt')
    with open(requirements_file, 'rt') as f:
        for line in f.readlines():
            opinel_requirements = re_opinel.match(line)
            if opinel_requirements:
                return opinel_requirements.groups()
    return None

#
# Connect to any service
#
def connect_service(service, credentials, region_name = None, config = None, silent = False):
    try:
        client_params = {}
        client_params['service_name'] = service.lower()
        session_params = {}
        session_params['aws_access_key_id'] = credentials['AccessKeyId']
        session_params['aws_secret_access_key'] = credentials['SecretAccessKey']
        session_params['aws_session_token'] = credentials['SessionToken']
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
            if entity in response:
                results[entity] = results[entity] + response[entity]
        if marker_name in response and response[marker_name]:
            params[marker_name] = response[marker_name]
        else:
            break
    return results

#
# Create key in dictionary if it doesn't exist
#
def manage_dictionary(dictionary, key, init, callback=None):
    if not str(key) in dictionary:
        dictionary[str(key)] = init
        manage_dictionary(dictionary, key, init)
        if callback:
            callback(dictionary[key])
    return dictionary

#
# Multithread generic helper
#
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

#
# Multithreaded get_region
#
def threaded_per_region(q, params):
    while True:
        try:
            params['region'] = q.get()
            method = params['method']
            method(params)
        except Exception as e:
            printException(e)
        finally:
            q.task_done()

########################################
# Credentials read/write functions
########################################

#
# Assume role and save credentials
#
def assume_role(role_name, credentials, role_arn, role_session_name):
    # Connect to STS
    sts_client = connect_service('sts', credentials, silent = False)
    # Set required arguments for assume role call
    sts_args = {
      'RoleArn': role_arn,
      'RoleSessionName': role_session_name
    }
    # MFA used ?
    if 'mfa_serial' in credentials and 'mfa_code' in credentials:
      sts_args['TokenCode'] = credentials['TokenCode']
      sts_args['SerialNumber'] = credentials['SerialNumber']
    # External ID used ?
    if 'ExternalId' in credentials and credentials['ExternalId']:
      sts_args['ExternalId'] = credentials['ExternalId']
    # Assume the role
    sts_response = sts_client.assume_role(**sts_args)
    credentials = sts_response['Credentials']
    cached_credentials_filename = get_cached_credentials_filename(role_name, role_arn)
    with open(cached_credentials_filename, 'wt+') as f:
        write_data_to_file(f, sts_response, True, False)
    return credentials

#
# Construct filepath for cached credentials (AWS CLI scheme)
#
def get_cached_credentials_filename(role_name, role_arn):
    filename_p1 = role_name.replace('/','-')
    filename_p2 = role_arn.replace('/', '-').replace(':', '_')
    return os.path.join(os.path.join(os.path.expanduser('~'), '.aws'), 'cli/cache/%s--%s.json' % (filename_p1, filename_p2))

#
# Create a dictionary with all the necessary keys set to "None"
#
def init_creds():
    return { 'AccessKeyId': None, 'SecretAccessKey': None, 'SessionToken': None, 'Expiration': None, 'SerialNumber': None, 'TokenCode': None }

#
# Fetch STS credentials
#
def init_sts_session(profile_name, credentials, duration = 28800, session_name = None, write_to_file = True):
    # Set STS arguments
    sts_args = {
        'DurationSeconds': duration
    }
    # Prompt for MFA code if MFA serial present
    if credentials['SerialNumber']:
        if not credentials['TokenCode']:
            credentials['TokenCode'] = prompt_4_mfa_code()
            if credentials['TokenCode'] == 'q':
                credentials['SerialNumber'] = None
        sts_args['TokenCode'] = credentials['TokenCode']
        sts_args['SerialNumber'] = credentials['SerialNumber']
    # Init session
    sts_client = boto3.session.Session(credentials['AccessKeyId'], credentials['SecretAccessKey']).client('sts')
    sts_response = sts_client.get_session_token(**sts_args)
    # Move long-lived credentials if needed
    if not profile_name.endswith('-nomfa') and credentials['AccessKeyId'].startswith('AKIA'):
        write_creds_to_aws_credentials_file(profile_name + '-nomfa', credentials)
    # Save STS values in the .aws/credentials file
    key_id = sts_response['Credentials']['AccessKeyId']
    secret = sts_response['Credentials']['SecretAccessKey']
    token = sts_response['Credentials']['SessionToken']
    expiration = sts_response['Credentials']['Expiration']
    if write_to_file:
        write_creds_to_aws_credentials_file(profile_name, sts_response['Credentials'])
    return sts_response['Credentials']

#
# Read credentials from anywhere (CSV, Environment, Instance metadata, config/credentials)
#
def read_creds(profile_name, csv_file = None, mfa_serial_arg = None, mfa_code = None, force_init = False, role_session_name = 'opinel'):
    first_sts_session = False
    expiration = None
    credentials = init_creds()
    if csv_file:
        # Read credentials from a CSV file that was provided
        credentials['AccessKeyId'], credentials['SecretAccessKey'], credentials['SerialNumber'] = read_creds_from_csv(csv_file)
    elif profile_name == 'default':
        # Try reading credentials from environment variables (Issue #11) if the profile name is 'default'
        credentials['AccessKeyId'], credentials['SecretAccessKey'], credentials['SessionToken'] = read_creds_from_environment_variables()
    if ('AccessKeyId' not in credentials or not credentials['AccessKeyId']) and not csv_file:
        # Read from EC2 instance metadata
        credentials['AccessKeyId'], credentials['SecretAccessKey'], credentials['SessionToken'] = read_creds_from_ec2_instance_metadata()
    if not credentials['AccessKeyId'] and not csv_file:
        # Lookup if a role is defined in ~/.aws/config
        role_arn, source_profile = read_profile_from_aws_config_file(profile_name)
        if not role_arn and not source_profile:
            # Lookup if a role is defined in ~/.aws/credentials
            role_arn, source_profile = read_profile_from_aws_config_file(profile_name, aws_credentials_file)
        if role_arn and source_profile:
            # Lookup cached credentials
            try:
                cached_credentials_filename = get_cached_credentials_filename(profile_name, role_arn)
                with open(cached_credentials_filename, 'rt') as f:
                    assume_role_data = json.load(f)
                    credentials = assume_role_data['Credentials']
                    expiration = dateutil.parser.parse(credentials['Expiration'])
                    expiration = expiration.replace(tzinfo=None)
                    current = datetime.datetime.utcnow()
                    if expiration < current:
                        print('Role\'s credentials have expired on %s' % credentials['Expiration'])
            except Exception as e:
                pass
            if not expiration or expiration < current or credentials['AccessKeyId'] == None:
                credentials = read_creds(source_profile)
                credentials = assume_role(profile_name, credentials, role_arn, role_session_name)
        # Read from ~/.aws/credentials
        else:
            credentials = read_creds_from_aws_credentials_file(profile_name)
            if credentials['SessionToken']:
                if 'Expiration' in credentials and credentials['Expiration']:
                    expiration = dateutil.parser.parse(credentials['Expiration'])
                    expiration = expiration.replace(tzinfo=None)
                    current = datetime.datetime.utcnow()
                    if expiration < current:
                        printInfo('Saved STS credentials expired on %s' % credentials['Expiration'])
                        force_init = True
                else:
                    force_init = True
            else:
                first_sts_session = True
            if force_init:
                credentials = read_creds_from_aws_credentials_file(profile_name if first_sts_session else '%s-nomfa' % profile_name)
                if mfa_serial_arg: 
                    credentials['SerialNumber'] = mfa_serial_arg
                if mfa_code:
                    credentials['TokenCode'] = mfa_code
                if 'AccessKeyId' in credentials and credentials['AccessKeyId']:
                    credentials = init_sts_session(profile_name, credentials)
    # If we don't have valid creds by now, print an error message
    if 'AccessKeyId' not in credentials or credentials['AccessKeyId'] == None or 'SecretAccessKey' not in credentials or credentials['SecretAccessKey'] == None:
        printError('Error: could not find AWS credentials. Use the --help option for more information.')
    if not 'AccessKeyId' in credentials:
        credentials = { 'AccessKeyId': None }
    return credentials
 

#
# Read credentials from AWS config file
#
def read_creds_from_aws_credentials_file(profile_name, credentials_file = aws_credentials_file):
    credentials = init_creds()
    profile_found = False
    try:
        # Make sure the ~.aws folder exists
        if not os.path.exists(aws_config_dir):
            os.makedirs(aws_config_dir)
        with open(credentials_file, 'rt') as cf:
            for line in cf:
                profile_line = re_profile_name.match(line)
                if profile_line:
                    if profile_line.groups()[0] == profile_name:
                        profile_found = True
                    else:
                        profile_found = False
                if profile_found:
                    if re_access_key.match(line):
                        credentials['AccessKeyId'] = line.split("=")[1].strip()
                    elif re_secret_key.match(line):
                        credentials['SecretAccessKey'] = line.split("=")[1].strip()
                    elif re_mfa_serial.match(line):
                        credentials['SerialNumber'] = (line.split('=')[1]).strip()
                    elif re_session_token.match(line):
                        credentials['SessionToken'] = ('='.join(x for x in line.split('=')[1:])).strip()
                    elif re_expiration.match(line):
                        credentials['Expiration'] = ('='.join(x for x in line.split('=')[1:])).strip()
    except Exception as e:
    # Silent if error is due to no ~/.aws/credentials file
        if e.errno != 2:
            printException(e)
        pass
    return credentials

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
                # Old CSV files were formatted as username, key_id, secret
                # New CSV files are formatted as key_id, secret
                # I authorized users to add their MFA serial after the secret
                creds = line.split(',')
                key_i = [i for (i, v) in enumerate(creds) if v.startswith('AKIA')]
                if len(key_i) == 1:
                    key_i = key_i[0]
                    key_id = creds[key_i].strip()
                    secret = creds[key_i + 1].strip()
                    mfa_serial = creds[key_i + 2].strip() if key_i + 2 < len(creds) else None
    return key_id, secret, mfa_serial

#
# Read credentials from EC2 instance metadata (IAM role)
#
def read_creds_from_ec2_instance_metadata():
    key_id = None
    secret = None
    token = None
    try:
        has_role = requests.get('http://169.254.169.254/latest/meta-data/iam/security-credentials', timeout = 1)
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
# Read profiles from AWS config file
#
def read_profile_from_aws_config_file(profile_name, config_file = aws_config_file):
    role_arn = None
    source_profile = None
    profile_found = False
    try:
        with open(config_file, 'rt') as config:
            for line in config:
                profile_line = re_profile_name.match(line)
                if profile_line:
                    role_profile_name = profile_line.groups()[0].split()[-1]
                    if role_profile_name == profile_name:
                        profile_found = True
                    else:
                        profile_found = False
                if profile_found:
                    if re_role_arn.match(line):
                        role_arn = line.split('=')[1].strip()
                    elif re_source_profile.match(line):
                        source_profile = line.split('=')[1].strip()
    except Exception as e:
    # Silent if error is due to no .aws/config file
        if e.errno != 2:
            printException(e)
        pass
    return role_arn, source_profile

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
def write_creds_to_aws_credentials_file(profile_name, credentials):
    profile_found = False
    profile_ever_found = False
    session_token_written = False
    security_token_written = False
    mfa_serial_written = False
    expiration_written = False
    # Create the .aws folder if needed
    if not os.path.isdir(aws_config_dir):
        os.mkdir(aws_config_dir)
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
                    if 'SessionToken' in credentials and credentials['SessionToken'] and not session_token_written:
                        print('aws_session_token = %s' % credentials['SessionToken'])
                        session_token_written = True
                    if 'SessionToken' in credentials and credentials['SessionToken'] and not security_token_written:
                        print('aws_security_token = %s' % credentials['SessionToken'])
                        security_token_written = True
                    if 'SerialNumber' in credentials and credentials['SerialNumber'] and not mfa_serial_written:
                        print('aws_mfa_serial = %s' % credentials['SerialNumber'])
                        mfa_serial_written = True
                    if 'Expiration' in credentials and credentials['Expiration'] and not expiration_written:
                        print('expiration = %s' % credentials['Expiration'])
                        expiration_written = True
                profile_found = False
            print(line.rstrip())
        elif profile_found:
            if re_access_key.match(line) and 'AccessKeyId' in credentials and credentials['AccessKeyId']:
                print('aws_access_key_id = %s' % credentials['AccessKeyId'])
            elif re_secret_key.match(line) and 'SecretAccessKey' in credentials and credentials['SecretAccessKey']:
                print('aws_secret_access_key = %s' % credentials['SecretAccessKey'])
            elif re_mfa_serial.match(line) and 'SerialNumber' in credentials and credentials['SerialNumber']:
                print('aws_mfa_serial = %s' % credentials['SerialNumber'])
                mfa_serial_written = True
            elif re_session_token.match(line) and 'SessionToken' in credentials and credentials['SessionToken']:
                print('aws_session_token = %s' % credentials['SessionToken'])
                session_token_written = True
            elif re_security_token.match(line) and 'SessionToken' in credentials and credentials['SessionToken']:
                print('aws_security_token = %s' % credentials['SessionToken'])
                security_token_written = True
            elif re_expiration.match(line) and 'Expiration' in credentials and credentials['Expiration']:
                print('expiration = %s' % credentials['Expiration'])
                expiration_written = True
            else:
                print(line.rstrip())
        else:
            print(line.rstrip())

    # Complete the profile if needed
    if profile_found and ('SessionToken' in credentials or 'SerialNumber' in credentials):
        with open(aws_credentials_file, 'a') as f:
            complete_profile(f, credentials['SessionToken'], session_token_written, credentials['SerialNumber'], mfa_serial_written)

    # Add new profile if not found
    if not profile_ever_found:
        with open(aws_credentials_file, 'a') as f:
            f.write('[%s]\n' % profile_name)
            f.write('aws_access_key_id = %s\n' % credentials['AccessKeyId'])
            f.write('aws_secret_access_key = %s\n' % credentials['SecretAccessKey'])
            complete_profile(f, credentials['SessionToken'], session_token_written, credentials['SerialNumber'], mfa_serial_written)

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


#
# Pass one condition?
# Needs to be here as used when loading IP ranges (Scout2 + various recipes)
#
def pass_condition(b, test, a):
    if test == 'inSubnets':
        grant = netaddr.IPNetwork(b)
        for c in a:
            known_subnet = netaddr.IPNetwork(c)
            if grant in known_subnet:
                return True
        return False
    if test == 'notInSubnets':
        grant = netaddr.IPNetwork(b)
        for c in a:
            known_subnet = netaddr.IPNetwork(c)
            if grant in known_subnet:
                return False
        return True
    elif test == 'containAction':
        if type(b) != dict:
            b = json.loads(b)
        actions = get_actions_from_statement(b)
        return True if a.lower() in actions else False
    elif test == 'isCrossAccount':
        if type(b) != list:
            b = [ b ]
        for c in b:
            if c == a or re.match(r'arn:aws:iam:.*?:%s:.*' % a, c):
                continue
            else:
                return True
        return False
    elif test == 'isSameAccount':
        if type(b) != list:
            b = [ b ]
        for c in b:
            if c == a or re.match(r'arn:aws:iam:.*?:%s:.*' % a, c):
                return True
            else:
                continue
        return False
    elif test == 'containOneMatching':
        if not type(b) == list:
            b = [ b ]
        for c in b:
            if re.match(a, c) != None:
                return True
        return False
    elif test == 'containAtLeastOneOf':
        if not type(b) == list:
            b = [ b ]
        for c in b:
            if type(c):
                c = str(c)
            if c in a:
                return True
        return False
    elif test == 'containAtLeastOneDifferentFrom':
        if not type(b) == list:
            b = [ b ]
        if not type(a) == list:
            a = [ a ]
        for c in b:
            if c not in a:
                return True
        return False
    elif test == 'containNoneOf':
        if not type(b) == list:
            b = [ b ]
        for c in b:
            if c in a:
                return False
        return True
    elif test == 'equal':
        if type(b) != str:
            b = str(b)
        return a == b
    elif test == 'notEqual':
        if type(b) != str:
            b = str(b)
        return a != b
    elif test == 'lessThan':
        return int(b) < int(a)
    elif test == 'lessOrEqual':
        return int(b) <= int(a)
    elif test == 'moreThan':
        return int(b) > int(a)
    elif test == 'moreOrEqual':
        return int(b) >= int(a)
    elif test == 'empty':
        return ((type(b) == dict and b == {}) or (type(b) == list and b == []) or (type(b) == list and b == [None]))
    elif test == 'notEmpty':
        return not ((type(b) == dict and b == {}) or (type(b) == list and b == []) or(type(b) == list and b == [None]))
    elif test == 'match':
        if type(b) != str:
            b = str(b)
        return re.match(a, b) != None
    elif test == 'notMatch':
        return re.match(a, b) == None
    elif test == 'null':
        return ((b == None) or (type(b) == str and b == 'None'))
    elif test == 'notNull':
        return not ((b == None) or (type(b) == str and b == 'None'))
    elif test == 'datePriorTo':
        b = dateutil.parser.parse(str(b)).replace(tzinfo=None)
        a = dateutil.parser.parse(str(a)).replace(tzinfo=None)
        return b < a
    elif test == 'dateOlderThan':
        try:
            age = (datetime.datetime.today() - dateutil.parser.parse(str(b)).replace(tzinfo=None)).days
            return age > int(a)
        except Exception as e:
            # Failure means an invalid date, meaning no activity
            printException(e)
            return True
    elif test == 'dateNotOlderThan':
        try:
            age = (datetime.datetime.today() - dateutil.parser.parse(b).replace(tzinfo=None)).days
            return age < int(a)
        except Exception as e:
            # Failure means an invalid date, meaning no activity
            return True
    elif test == 'true':
        return b in [True, 'True', 'true']
    elif test == 'notTrue' or test == 'false':
        return b not in [True, 'True', 'true']
    elif test == 'withKey':
        return a in b
    elif test == 'withoutKey':
        return not a in b
    elif test == 'inRange':
        range_found = re_port_range.match(b)
        if range_found:
            p1 = int(range_found.group(1))
            p2 = int(range_found.group(2))
            if int(a) in range(int(range_found.group(1)), int(range_found.group(2))):
                return True
        else:
            port_found = re_single_port.match(b)
            if port_found and a == port_found.group(1):
                return True
    elif test == 'lengthLessThan':
        return len(b) < int(a)
    elif test == 'lengthMoreThan':
        return len(b) > int(a)
    elif test == 'lengthEqual':
        return len(b) == int(a)
    else:
        # Throw an exception here actually...
        printError('Error: unknown test case %s' % test)
    return False
