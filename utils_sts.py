#!/usr/bin/env python2

# Import AWS utils
from AWSUtils.utils_iam import *


########################################
##### Helpers
########################################

#
# Fetch STS credentials and store them in a file
#
def init_sts_session_and_save_in_credentials(profile_name, credentials_file = aws_credentials_file_no_mfa, mfa_code = None, mfa_serial_arg = None):
    save_no_mfa_credentials = False
    try:
        # Parse no-MFA config
        key_id, secret, mfa_serial, session_token = read_creds_from_aws_credentials_file(profile_name, credentials_file = credentials_file)
        if not key_id or not secret:
            # Parse normal config
            key_id, secret, mfa_serial, session_token = read_creds_from_aws_credentials_file(profile_name)
            if not key_id or not secret:
                print 'Error, could not find credentials for profile \'%s\'.' % profile_name
                return False
            else:
                save_no_mfa_credentials = True
        # If an MFA serial was provided as an argument, discard whatever we found in config file
        if mfa_serial_arg:
            mfa_serial = mfa_serial_arg
        session_access_key, session_secret_key, session_token = init_sts_session(key_id, secret, mfa_serial, mfa_code)
        if save_no_mfa_credentials:
            # Write long-lived credentials to the no-MFA config file
            write_creds_to_aws_credentials_file(profile_name, key_id = key_id, secret = secret, mfa_serial = mfa_serial, credentials_file = aws_credentials_file_no_mfa)
        # Write the new credentials to the config file
        write_creds_to_aws_credentials_file(profile_name, key_id = session_access_key, secret = session_secret_key, session_token = session_token)
        # Success
        print 'Successfully configured the session token for profile \'%s\'.' % profile_name
        return True
    except Exception, e:
        printException(e)
        return False


########################################
##### STS-related arguments
########################################

parser.add_argument('--mfa_serial',
                    dest='mfa_serial',
                    default=[ None ],
                    nargs='+',
                    help='MFA device\'s serial number')
parser.add_argument('--mfa_code',
                    dest='mfa_code',
                    default=[''],
                    nargs='+',
                    help='MFA code')
