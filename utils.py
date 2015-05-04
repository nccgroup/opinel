#!/usr/bin/env python2

# Import third-party packages
import argparse
import boto
from distutils import dir_util
import copy
import json
import os
import re
import requests
import shutil
import sys
import traceback
import urllib2


########################################
# Globals
########################################

re_profile_name = re.compile(r'\[.*]')
re_access_key = re.compile(r'aws_access_key_id')
re_secret_key = re.compile(r'aws_secret_access_key')
re_mfa_serial = re.compile(r'aws_mfa_serial')
re_session_token = re.compile(r'aws_session_token')
mfa_serial_format = r'^arn:aws:iam::\d+:mfa/[a-zA-Z0-9\+=,.@_-]+$'
re_mfa_serial_format = re.compile(mfa_serial_format)

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

def check_boto_version():
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


########################################
# Credentials read/write functions
##################################s######

#
# Prompt for MFA code
#
def prompt_4_mfa_code():
    while True:
        mfa_code = prompt_4_value('Enter your MFA code: ')
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
                    if re.match(r'aws_access_key_id', line):
                        key_id = (line.split(' ')[2]).rstrip()
                    elif re.match(r'aws_secret_access_key', line):
                        secret = (line.split(' ')[2]).rstrip()
                    elif re_mfa_serial.match(line):
                        mfa_serial = (line.split(' ')[2]).rstrip()
                    elif re.match(r'aws_session_token', line):
                        security_token = (line.split(' ')[2]).rstrip()
    except Exception, e:
        pass
    return key_id, secret, mfa_serial, security_token

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
# Legacy AWS Credentials read functions
########################################

aws_config_file = os.path.join(os.path.join(os.path.expanduser('~'),'.aws'), 'config')
boto_config_file = os.path.join(os.path.join(os.path.expanduser('~'), '.aws'), 'credentials')

def fetch_creds_from_instance_metadata():
    base_url = 'http://169.254.169.254/latest/meta-data/iam/security-credentials'
    try:
        iam_role = urllib2.urlopen(base_url).read()
        credentials = json.loads(urllib2.urlopen(base_url + '/' + iam_role).read())
        return credentials['AccessKeyId'], credentials['SecretAccessKey'], credentials['Token']
    except Exception, e:
        print 'Failed to fetch credentials. Make sure that this EC2 instance has an IAM role (%s)' % e
        return None, None, None

def fetch_creds_from_csv(filename):
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

def fetch_creds_from_aws_cli_config(config_file, profile_name):
    key_id = None
    secret = None
    session_token = None
    re_new_profile = re.compile(r'\[\w+\]')
    re_use_profile = re.compile(r'\[%s\]' % profile_name)
    with open(config_file, 'rt') as config:
        for line in config:
            if re_use_profile.match(line):
                profile_found = True
            elif re_new_profile.match(line):
                profile_found = False
            if profile_found:
                if re.match(r'aws_access_key_id', line):
                    key_id = line.split(' ')[2]
                elif re.match(r'aws_secret_access_key', line):
                    secret = line.split(' ')[2]
                elif re.match(r'aws_session_token', line):
                    session_token = line.split(' ')[2]
    return key_id, secret, session_token

def fetch_creds_from_system(profile_name):
    key_id = None
    secret = None
    session_token = None
    # Check environment variables
    if 'AWS_ACCESS_KEY_ID' in os.environ and 'AWS_SECRET_ACCESS_KEY' in os.environ:
        key_id = os.environ['AWS_ACCESS_KEY_ID']
        secret = os.environ['AWS_SECRET_ACCESS_KEY']
        if 'AWS_SESSION_TOKEN' in os.environ:
            session_token = os.environ['AWS_SESSION_TOKEN']
    # Search for a Boto config file
    elif os.path.isfile(boto_config_file):
        key_id, secret, session_token = fetch_creds_from_aws_cli_config(boto_config_file, profile_name)
    # Search for an AWS CLI config file
    elif os.path.isfile(aws_config_file):
        print 'Found an AWS CLI configuration file at %s' % aws_config_file
        if prompt_4_yes_no('Would you like to use the credentials from this file?'):
            key_id, secret, session_token = fetch_creds_from_aws_cli_config(aws_config_file, profile_name)
    # Search for EC2 instance metadata
    else:
        metadata = boto.utils.get_instance_metadata(timeout=1, num_retries=1)
        if metadata:
            key_id, secret, session_token = fetch_creds_from_instance_metadata()
    if session_token:
        session_token = session_token.rstrip()
    return key_id.rstrip(), secret.rstrip(), session_token

def fetch_sts_credentials(key_id, secret, mfa_serial, mfa_code):
    if not mfa_serial or len(mfa_serial) < 1:
        print 'Error, you need to provide your MFA device\'s serial number.'
        return None, None, None
    if not mfa_code or len(mfa_code) < 1:
        print 'Error, you need to provide the code displayed by your MFA device.'
        return None, None, None
    sts_connection = boto.connect_sts(key_id, secret)
    # For now, don't set the duration and use default 12hours
    sts_response = sts_connection.get_session_token(mfa_serial_number = mfa_serial, mfa_token = mfa_code[0])
    return sts_response.access_key, sts_response.secret_key, sts_response.session_token
