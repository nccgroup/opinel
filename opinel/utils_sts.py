
# Import opinel
from opinel.utils import *


########################################
##### STS-related arguments
########################################

#
# Add an STS-related argument to a recipe
#
def add_sts_argument(parser, argument_name):
    if argument_name == 'mfa-serial':
        parser.add_argument('--mfa-serial',
                            dest='mfa_serial',
                            default=[ None ],
                            nargs='+',
                            help='MFA device\'s serial number')
    elif argument_name == 'mfa-code':
        parser.add_argument('--mfa-code',
                            dest='mfa_code',
                            default=[ None ],
                            nargs='+',
                            help='MFA code')
    else:
        raise Exception('Invalid parameter name: %s' % argument_name)


########################################
##### Helpers
########################################

#
# Get role credentials
#
def assume_role(sts_client, role_arn, role_session_name, mfa_serial = None, mfa_code = None):
    if mfa_serial and mfa_code:
        sts_response = sts_client.assume_role(RoleArn = role_arn, RoleSessionName = role_session_name, SerialNumber = mfa_serial, TokenCode = mfa_code)
    else:
        sts_response = sts_client.assume_role(RoleArn = role_arn, RoleSessionName = role_session_name)
    return sts_response['Credentials']['AccessKeyId'], sts_response['Credentials']['SecretAccessKey'], sts_response['Credentials']['SessionToken']

#
# Fetch role credentials and store them in a file
#
def assume_role_and_save_in_credentials(profile_name, role_arn, role_session_name, mfa_serial_arg, mfa_code):

    # Init
    key_id = secret = mfa_serial = session_token = None
    save_no_mfa_credentials = False

    # Search credentials
    key_id, secret, mfa_serial, session_token = read_creds_from_aws_credentials_file(profile_name)

    # If nothing found, search for long-lived credentials stored as -nomfa
    if (not key_id or not secret) and not profile_name.endswith('-nomfa'):
        key_id, secret, mfa_serial, session_token = read_creds_from_aws_credentials_file(profile_name + '-nomfa')
        save_no_mfa_credentials = True

    if not key_id or not secret:
        raise Exception('Error: could not find AWS credentials. Use the --help option for more information.')

    # If an MFA serial was provided as an argument, discard whatever we found in config file
    if mfa_serial_arg:
        mfa_serial = mfa_serial_arg

    # Prompt for a token code if needed
    if mfa_serial and not mfa_code and not session_token:
        mfa_code = prompt_4_mfa_code()

    sts_client = connect_sts(key_id, secret, session_token)
    role_key_id, role_secret, role_session_token = assume_role(sts_client, role_arn, role_session_name, mfa_serial, mfa_code)

    # Save session credentials
    role_profile = profile_name.replace('-nomfa', '') + '-' + role_session_name
    write_creds_to_aws_credentials_file(role_profile, key_id = role_key_id, secret = role_secret, session_token = role_session_token)

    printInfo('Your role credentials have been saved in the %s profile.' % role_profile)

#
# Connect to STS
#
def connect_sts(key_id, secret, session_token):
    try:
        printInfo('Connecting to AWS STS...')
        return boto3.client('sts', aws_access_key_id = key_id, aws_secret_access_key = secret, aws_session_token = session_token)
    except Exception as e:
        printError('Error: could not connect to STS.')
        printException(e)
        return None

#
# Fetch STS credentials and store them in a file
#
def init_sts_session_and_save_in_credentials(profile_name, credentials_file = aws_credentials_file, mfa_code = None, mfa_serial_arg = None):

    # Init
    key_id = secret = mfa_serial = session_token = None
    save_no_mfa_credentials = False

    # First check for long-lived credentials stored under <profile_name>-nomfa
    if not mfa_serial_arg and not profile_name.endswith('-nomfa'):
        key_id, secret, mfa_serial, session_token = read_creds_from_aws_credentials_file(profile_name + '-nomfa')

    # If nothing found or the mfa serial was provided, search with the provided profile name
    if not key_id or not secret:
        key_id, secret, mfa_serial, session_token = read_creds_from_aws_credentials_file(profile_name)
        save_no_mfa_credentials = True

    if not key_id or not secret:
        raise Exception('Error: could not find AWS credentials. Use the --help option for more information.')

    if mfa_serial == mfa_serial_arg == None:
        raise Exception('Error: you must provide an MFA device serial number to receive STS credentials. Update your credentials file or use the --serial_number argument.')

    # If an MFA serial was provided as an argument, discard whatever we found in config file
    if mfa_serial_arg:
        mfa_serial = mfa_serial_arg

    # Get STS credentials
    session_access_key, session_secret_key, session_token = init_sts_session(key_id, secret, mfa_serial, mfa_code)

    # Save long-lived credentials if needed
    if save_no_mfa_credentials:
        write_creds_to_aws_credentials_file(profile_name + '-nomfa', key_id = key_id, secret = secret, mfa_serial = mfa_serial)

    # Save session credentials
    write_creds_to_aws_credentials_file(profile_name, key_id = session_access_key, secret = session_secret_key, session_token = session_token)

    # Success
    printInfo('Successfully configured the session token for profile \'%s\'.' % profile_name)
