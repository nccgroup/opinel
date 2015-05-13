#!/usr/bin/env python2

# Import third-party packages
import argparse
import boto
from boto import utils
import copy
from distutils import dir_util
import json
import fileinput
import os
from Queue import Queue
import re
import requests
import shutil
import sys
from threading import Event, Thread
import traceback
import urllib2

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
re_gov_region = re.compile(r'(.*)?-gov-(.*)?')
re_cn_region = re.compile(r'^cn-(.*)?')

aws_credentials_file = os.path.join(os.path.join(os.path.expanduser('~'), '.aws'), 'credentials')
aws_credentials_file_no_mfa = os.path.join(os.path.join(os.path.expanduser('~'), '.aws'), 'credentials.no-mfa')
aws_credentials_file_tmp = os.path.join(os.path.join(os.path.expanduser('~'), '.aws'), 'credentials.tmp')


########################################
##### Argument parser
########################################

def init_parser():
    if not 'parser' in globals():
        global parser
        parser = argparse.ArgumentParser()

init_parser()
parser.add_argument('--debug',
                    dest='debug',
                    default=False,
                    action='store_true',
                    help='Print the stack trace when exception occurs')
parser.add_argument('--profile',
                    dest='profile',
                    default= [ 'default' ],
                    nargs='+',
                    help='Name of the profile')


########################################
##### Debug-related functions
########################################

def printException(e):
    global verbose_exceptions
    if verbose_exceptions:
        print traceback.format_exc()
    else:
        print e

def configPrintException(enable):
    global verbose_exceptions
    verbose_exceptions = enable


########################################
# Common functions
########################################

#
# Build the list of target region names
#
def build_region_list(boto_regions, chosen_regions = [], include_gov = False, include_cn = False):
    boto_region_names = []
    for region in boto_regions:
        if (not re_gov_region.match(region.name) or include_gov) and (not re_cn_region.match(region.name) or include_cn):
            boto_region_names.append(region.name)
    if len(chosen_regions):
        return list((Counter(boto_region_names) & Counter(chosen_regions)).elements())
    else:
        return boto_region_names

def check_boto_version():
    print 'Checking the version of boto...'
    min_boto_version = '2.31.1'
    latest_boto_version = 0
    if boto.Version < min_boto_version:
        print 'Error: the version of boto installed on this system (%s) is too old. Boto version %s or newer is required.' % (boto.Version, min_boto_version)
        return False
    else:
        try:
            # Warn users who have not the latest version of boto installed
            release_tag_regex = re.compile('(\d+)\.(\d+)\.(\d+)')
            tags = requests.get('https://api.github.com/repos/boto/boto/tags').json()
            for tag in tags:
                if release_tag_regex.match(tag['name']) and tag['name'] > latest_boto_version:
                    latest_boto_version = tag['name']
            if boto.Version < latest_boto_version:
                print 'Warning: the version of boto installed (%s) is not the latest available (%s). Consider upgrading to ensure that all features are enabled.' % (boto.Version, latest_boto_version)
        except Exception, e:
            print 'Warning: connection to the Github API failed.'
            printException(e)
    return True

def get_environment_name(args):
    environment_name = None
    if 'profile' in args and args.profile[0] != 'default':
        environment_name = args.profile[0]
    elif args.environment_name:
        environment_name = args.environment_name[0]
    return environment_name

def manage_dictionary(dictionary, key, init, callback=None):
    if not str(key) in dictionary:
        dictionary[str(key)] = init
        manage_dictionary(dictionary, key, init)
        if callback:
            callback(dictionary[key])
    return dictionary

def thread_work(connection_info, service_info, targets, function, display_function = None, service_params = {}, num_threads = 0):
    if display_function:
        # Status
        stop_display_thread = Event()
        display_thread = Thread(target=display_function, args=(service_info, stop_display_thread,))
        display_thread.start()
    # Init queue and threads
    q = Queue(maxsize=0)
    if not num_threads:
        num_threads = len(targets)
    for i in range(num_threads):
        worker = Thread(target=function, args=(connection_info, q, service_params))
        worker.setDaemon(True)
        worker.start()
    for target in targets:
        q.put([service_info, target])
    q.join()
    if display_function:
        stop_display_thread.set()

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
    sts_connection = boto.connect_sts(key_id, secret)
    sts_response = sts_connection.get_session_token(mfa_serial_number = mfa_serial, mfa_token = mfa_code, duration = 28800)
    return sts_response.access_key, sts_response.secret_key, sts_response.session_token

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
    # If we have an MFA serial number or MFA code and no token yet, initiate an STS session
    if (mfa_serial or mfa_code) and not token:
        key_id, secret, token = init_sts_session(key_id, secret, mfa_serial, mfa_code)
    return key_id, secret, token

#
# Read credentials from AWS config file
#
def read_creds_from_aws_credentials_file(profile_name, credentials_file = aws_credentials_file):
    key_id = None
    secret = None
    mfa_serial = None
    security_token = None
    re_use_profile = re.compile(r'\[%s\]' % profile_name)
    try:
        with open(credentials_file, 'rt') as credentials:
            for line in credentials:
                if re_use_profile.match(line):
                    profile_found = True
                elif re_profile_name.match(line):
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
    except Exception, e:
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
                        print 'Error, the CSV file is not properly formatted'
    return key_id.rstrip(), secret.rstrip(), mfa_serial

#
# Read credentials from EC2 instance metadata (IAM role)
#
def read_creds_from_ec2_instance_metadata():
    key_id = None
    secret = None
    token = None
    metadata = boto.utils.get_instance_metadata(timeout=1, num_retries=1)
    if metadata:
        for role in metadata['iam']['security-credentials']:
            key_id = metadata['iam']['security-credentials'][role]['AccessKeyId']
            secret = metadata['iam']['security-credentials'][role]['SecretAccessKey']
            token = metadata['iam']['security-credentials'][role]['Token']
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
    # h4ck to have an early read of the profile name
    for i, arg in enumerate(sys.argv):
        if arg == '--profile' and len(sys.argv) >= i + 1:
            profile_name = sys.argv[i + 1]
    saved_args = {}
    recipes_dir = os.path.join(os.path.join(os.path.expanduser('~'), '.aws'), 'recipes')
    recipe_file = os.path.join(recipes_dir, profile_name + '.json')
    if os.path.isfile(recipe_file):
        with open(recipe_file, 'rt') as f:
            config = json.load(f)
        t = re.compile(r'(.*)?\.py')
        for key in config:
            if not t.match(key):
                saved_args[key] = config[key]
            elif key == parser.prog:
                saved_args.update(config[key])
    return saved_args

#
# Returns the argument default value, customized by the user or default programmed value
#
def set_profile_default(saved_args, key, default):
    return saved_args[key] if key in saved_args else default

#
# Show profile names from ~/.aws/credentials and ~/.aws/credentials.no-mfa
#
def show_profiles_from_aws_credentials_file():
    profiles = []
    files = [ aws_credentials_file, aws_credentials_file_no_mfa ]
    for filename in files:
        if os.path.isfile(filename):
            with open(filename) as f:
                lines = f.readlines()
                for line in lines:
                    groups = re_profile_name.match(line)
                    if groups:
                        profiles.append(groups.groups()[0])
    for profile in set(profiles):
        print ' * %s' % profile

#
# Write credentials to AWS config file
#
def write_creds_to_aws_credentials_file(profile_name, key_id = None, secret = None, session_token = None, mfa_serial = None, credentials_file = aws_credentials_file):
    re_profile = re.compile(r'\[%s\]' % profile_name)
    profile_found = False
    profile_ever_found = False
    session_token_written = False
    mfa_serial_written = False
    if not os.path.isfile(credentials_file):
        if os.path.isfile(aws_credentials_file_no_mfa):
            # copy credentials.no-mfa if target file does not exist
            shutil.copyfile(aws_credentials_file_no_mfa, credentials_file)
        else:
            # Create an empty file if credentials.no-mfa does not exist
            open(credentials_file, 'a').close()
    # Open and parse/edit file
    for line in fileinput.input(credentials_file, inplace=True):
        if re_profile_name.match(line):
            if profile_name in line:
                profile_found = True
                profile_ever_found = True
            else:
                if profile_found:
                    if session_token and not session_token_written:
                        print 'aws_session_token = %s' % session_token
                        session_token_written = True
                    if mfa_serial and not mfa_serial_written:
                        print 'aws_mfa_serial = %s' % mfa_serial
                        mfa_serial_written = True
                profile_found = False
            print line.rstrip()
        elif profile_found:
            if re_access_key.match(line) and key_id:
                print 'aws_access_key_id = %s' % key_id
            elif re_secret_key.match(line) and secret:
                print 'aws_secret_access_key = %s' % secret
            elif re_mfa_serial.match(line) and mfa_serial:
                print 'aws_mfa_serial = %s' % mfa_serial
                mfa_serial_written = True
            elif re_session_token.match(line) and session_token:
                print 'aws_session_token = %s' % session_token
                session_token_written = True
            else:
                print line.rstrip()
        else:
            print line.rstrip()

    # Complete the profile if needed
    if profile_found:
        with open(credentials_file, 'a') as f:
            complete_profile(f, session_token, session_token_written, mfa_serial, mfa_serial_written)

    # Add new profile if only found in .no-mfa configuration file
    if not profile_ever_found:
        with open(credentials_file, 'a') as f:
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
def prompt_4_mfa_code():
    while True:
        mfa_code = prompt_4_value('Enter your MFA code: ', no_confirm = True)
        try:
            int(mfa_code)
            mfa_code[5]
            break
        except:
            print 'Error, your MFA code must only consist of digits and be at least 6 characters long'
    return mfa_code

#
# Prompt for MFA serial
#
def prompt_4_mfa_serial():
    while True:
        mfa_serial = prompt_4_value('Enter your MFA serial: ')
        if re_mfa_serial_format.match(mfa_serial):
            break
        else:
            print 'Error, your MFA serial must be of the form %s' % mfa_serial_format
    return mfa_serial

#
# Prompt for a value
#
def prompt_4_value(question, choices = None, default = None, display_choices = True, display_indices = False, authorize_list = False, is_question = False, no_confirm = False):
    if choices and len(choices) == 1 and choices[0] == 'yes_no':
        return prompt_4_yes_no(question)
    if choices and display_choices and not display_indices:
        question = question + ' (' + '/'.join(choices) + ')'
    while True:
        if choices and display_indices:
            for c in choices:
                print '%3d. %s' % (choices.index(c), c)
        if is_question:
            question = question + '? '
	sys.stdout.write(question)
        choice = raw_input()
        if choices:
            user_choices = choice.split(',')
            if not authorize_list and len(user_choices) > 1:
                print 'Multiple values are not supported; please enter a single value.'
            else:
                choice_valid = True
                if display_indices and int(choice) < len(choices):
                    choice = choices[int(choice)]
                else:
                    for c in user_choices:
                        if not c in choices:
                            print 'Invalid value (%s).' % c
                            choice_valid = False
                            break
                if choice_valid:
                    return choice
        elif not choice and default:
            if prompt_4_yes_no('Use the default value (' + default + ')'):
                return default
        elif not choice:
            print 'You cannot leave this parameter empty.'
        elif no_confirm or prompt_4_yes_no('You entered "' + choice + '". Is that correct'):
            return choice

#
# Prompt for yes/no answer
#
def prompt_4_yes_no(question):
    while True:
        sys.stdout.write(question + ' (y/n)? ')
        choice = raw_input().lower()
        if choice == 'yes' or choice == 'y':
            return True
        elif choice == 'no' or choice == 'n':
            return False
        else:
            print '\'%s\' is not a valid answer. Enter \'yes\'(y) or \'no\'(n).' % choice
