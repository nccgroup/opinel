
# Import opinel
from opinel.utils import *

# Import stock packages
import base64
from collections import Counter
import fileinput
import os
import re
import shutil
import tempfile
import webbrowser

# Import third-party packages
_fabulous_available = True
try:
    import fabulous.utils
    import fabulous.image
    # fabulous does not import its PIL dependency on import time, so
    # force it to check them now so we know whether it's really usable
    # or not.  If it can't import PIL it raises ImportError.
    fabulous.utils.pil_check()
except ImportError:
    _fabulous_available = False
    pass


########################################
##### IAM-related arguments
########################################

#
# Add an IAM-related argument to a recipe
#
def add_iam_argument(parser, default_args, argument_name):
    if argument_name == 'user-name':
        parser.add_argument('--user-name',
                            dest='user_name',
                            default=[ None ],
                            nargs='+',
                            help='Your AWS IAM user name; if not provided, this script will find it automatically if you have iam:getUser privileges')
    elif argument_name == 'category-groups':
        parser.add_argument('--category-groups',
                            dest='category_groups',
                            default=set_profile_default(default_args, 'category_groups', []),
                            nargs='+',
                            help='Choice of groups that all IAM users should belong to')
    elif argument_name == 'common-groups':
        parser.add_argument('--common-groups',
                            dest='common_groups',
                            default=set_profile_default(default_args, 'common_groups', []),
                            nargs='+',
                            help='Groups that all IAM users should belong to')
    elif argument_name == 'csv-credentials':
        parser.add_argument('--csv-credentials',
                    dest='csv_credentials',
                    default=[ None ],
                    nargs='+',
                    help='Read credentials from a CSV file')
    else:
        raise Exception('Invalid parameter name: %s' % argument_name)


########################################
##### Helpers
########################################

#
# Add an IAM user to an IAM group and updates the user info if needed
#
def add_user_to_group(iam_client, group, user, user_info = None, dry_run = False):
    if not dry_run:
        iam_client.add_user_to_group(GroupName = group, UserName = user)
    if user_info != None:
        user_info[user]['groups'].append(group)

#
# Add an IAM user to a category group if he doesn't belong to one already
#
def add_user_to_category_group(iam_client, current_groups, category_groups, category_regex, user, user_info = None, dry_run = False):
        category_memberships = list((Counter(current_groups) & Counter(category_groups)).elements())
        if not len(category_memberships):
            group = None
            sys.stdout.write('User \'%s\' does not belong to any of the category group (%s). ' % (user, ', '.join(category_groups)))
            sys.stdout.flush()
            if len(category_regex):
                group = get_category_group_from_user_name(user, category_groups, category_regex)
                if not group:
                    sys.stdout.write('Failed to determine the category group based on the user name.\n')
                    sys.stdout.flush()
                else:
                    sys.stdout.write('Automatically adding...\n')
                    add_user_to_group(iam_client, group, user, user_info, dry_run)
                sys.stdout.flush()
            if not group and prompt_4_yes_no('Do you want to remediate this now'):
                group = prompt_4_value('Which category group should \'%s\' belong to' % user, choices = category_groups, display_choices = True, display_indices = True, is_question = True)
                add_user_to_group(iam_client, group, user, user_info, dry_run)

#
# Add an IAM user to the common group(s) if he's not yet a member
#
def add_user_to_common_group(iam_client, current_groups, common_groups, user, force_common_group, user_info = None, dry_run = False):
    mandatory_memberships = list((Counter(current_groups) & Counter(common_groups)).elements())
    for group in common_groups:
        if group not in mandatory_memberships:
            sys.stdout.write('User \'%s\' does not belong to the mandatory common group \'%s\'. ' % (user, group))
            sys.stdout.flush()
            if force_common_group == True:
                sys.stdout.write('Automatically adding...\n')
                add_user_to_group(iam_client, group, user, user_info, dry_run)
            elif prompt_4_yes_no('Do you want to remediate this now'):
                add_user_to_group(iam_client, group, user, user_info, dry_run)
            sys.stdout.flush()

#
# Connect to IAM
#
def connect_iam(key_id, secret, session_token, silent = False):
    return connect_service('IAM', key_id, secret, session_token, silent)

#
# Create default groups
#
def create_default_groups(iam_client, common_groups, category_groups, dry_run):
    all_groups = common_groups + category_groups
    for group in all_groups:
        try:
            printInfo('Creating group \'%s\'...' % group)
            if not dry_run:
                iam_client.create_group(GroupName = group)
        except Exception as e:
            printException(e)
            pass

#
# Create and activate an MFA virtual device
#
def enable_mfa(iam_client, user, qrcode_file = None):
    mfa_serial = ''
    tmp_qrcode_file = None
    try:
        printInfo('Enabling MFA for user \'%s\'...' % user)
        mfa_device = iam_client.create_virtual_mfa_device(VirtualMFADeviceName = user)['VirtualMFADevice']
        mfa_serial = mfa_device['SerialNumber']
        mfa_png = mfa_device['QRCodePNG']
        mfa_seed = mfa_device['Base32StringSeed']
        tmp_qrcode_file = display_qr_code(mfa_png, mfa_seed)
        if qrcode_file != None:
            with open(qrcode_file, 'wt') as f:
                f.write(mfa_png)
        while True:
            mfa_code1 = prompt_4_mfa_code()
            mfa_code2 = prompt_4_mfa_code(activate = True)
            if mfa_code1 == 'q' or mfa_code2 == 'q':
                try:
                    delete_virtual_mfa_device(iam_client, mfa_serial)
                except Exception as e:
                    printException(e)
                    pass
                raise Exception
            try:
                iam_client.enable_mfa_device(UserName = user, SerialNumber = mfa_serial, AuthenticationCode1= mfa_code1, AuthenticationCode2 = mfa_code2)
                printInfo('Succesfully enabled MFA for for \'%s\'. The device\'s ARN is \'%s\'.' % (user, mfa_serial))
                break
            except Exception as e:
                printException(e)
                pass
    except Exception as e:
        printException(e)
        # We shouldn't return normally because if we've gotten here
        # the user has potentially not set up the MFA device
        # correctly, so we don't want to e.g. write the .no-mfa
        # credentials file or anything.
        raise
    finally:
        if tmp_qrcode_file is not None:
            # This is a tempfile.NamedTemporaryFile, so simply closing
            # it will also unlink it.
            tmp_qrcode_file.close()
    return mfa_serial

#
# Delete IAM user
#
def delete_user(iam_client, user, mfa_serial = None):
    printInfo('Deleting user %s...' % user)
    # Delete access keys
    try:
        aws_keys = get_all_access_keys(iam_client, user)
        for aws_key in aws_keys:
            try:
                printInfo('Deleting access key ID %s... ' % aws_key['AccessKeyId'], False)
                iam_client.delete_access_key(AccessKeyId = aws_key['AccessKeyId'], UserName = user)
                printInfo('Success')
            except Exception as e:
                printInfo('Failed')
                printException(e)
    except Exception as e:
        printException(e)
        printError('Failed to get access keys for user %s.' % user)
    # Deactivate and delete MFA devices
    try:
        mfa_devices = iam_client.list_mfa_devices(UserName = user)['MFADevices']
        for mfa_device in mfa_devices:
            serial = mfa_device['SerialNumber']
            try:
                printInfo('Deactivating MFA device %s... ' % serial, False)
                iam_client.deactivate_mfa_device(SerialNumber = serial, UserName = user)
                printInfo('Success')
            except Exception as e:
                printInfo('Failed')
                printException(e)
            delete_virtual_mfa_device(iam_client, serial)
        if mfa_serial:
            delete_virtual_mfa_device(iam_client, mfa_serial)
    except Exception as e:
        printException(e)
        printError('Failed to fetch MFA device serial number for user %s.' % user)
        pass
    # Remove IAM user from groups
    try:
        groups = iam_client.list_groups_for_user(UserName = user)['Groups']
        for group in groups:
            try:
                printInfo('Removing from group %s... ' % group['GroupName'], False)
                iam_client.remove_user_from_group(GroupName = group['GroupName'], UserName = user)
                printInfo('Success')
            except Exception as e:
                printInfo('Failed')
                printException(e)
    except Exception as e:
        printException(e)
        printError('Failed to fetch IAM groups for user %s.' % user)
        pass
    # Delete login profile
    login_profile = []
    try:
        login_profile = iam_client.get_login_profile(UserName = user)['LoginProfile']
    except Exception as e:
        pass
    try:
        if len(login_profile):
            printInfo('Deleting login profile... ', False)
            iam_client.delete_login_profile(UserName = user)
            printInfo('Success')
    except Exception as e:
        printInfo('Failed')
        printException(e)
        pass
    # Delete inline policies
    try:
        printInfo('Deleting inline policies... ', False)
        policies = iam_client.list_user_policies(UserName = user)
        for policy in policies['PolicyNames']:
            iam_client.delete_user_policy(UserName = user, PolicyName = policy)
        printInfo('Success')
    except Exception as e:
        printInfo('Failed')
        printException(e)
        pass   
    # Detach managed policies
    try:
        printInfo('Detaching managed policies... ', False)
        policies = iam_client.list_attached_user_policies(UserName = user)
        for policy in policies['AttachedPolicies']:
            iam_client.detach_user_policy(UserName = user, PolicyArn = policy['PolicyArn'])
        printInfo('Success')
    except Exception as e:
        printInfo('Failed')
        printException(e)
    # Delete IAM user
    try:
        iam_client.delete_user(UserName = user)
        printInfo('User %s deleted.' % user)
    except Exception as e:
        printException(e)
        printError('Failed to delete user.')
        pass

#
# Delete a vritual MFA device given its serial number
#
def delete_virtual_mfa_device(iam_client, mfa_serial):
    try:
        printInfo('Deleting MFA device %s...' % mfa_serial)
        iam_client.delete_virtual_mfa_device(SerialNumber = mfa_serial)
    except Exception as e:
        printException(e)
        printError('Failed to delete MFA device %s' % mfa_serial)
        pass   

#
# Display MFA QR code
#
def display_qr_code(png, seed):
    # This NamedTemporaryFile is deleted as soon as it is closed, so
    # return it to caller, who must close it (or program termination
    # could cause it to be cleaned up, that's fine too).
    # If we don't keep the file around until after the user has synced
    # his MFA, the file will possibly be already deleted by the time
    # the operating system gets around to execing the browser, if
    # we're using a browser.
    qrcode_file = tempfile.NamedTemporaryFile(suffix='.png', delete=True, mode='wt')
    qrcode_file.write(png)
    qrcode_file.flush()
    if _fabulous_available:
        fabulous.utils.term.bgcolor = 'white'
        with open(qrcode_file.name, 'rb') as png_file:
            print(fabulous.image.Image(png_file, 100))
    else:
        graphical_browsers = [webbrowser.BackgroundBrowser,
                              webbrowser.Mozilla,
                              webbrowser.Galeon,
                              webbrowser.Chrome,
                              webbrowser.Opera,
                              webbrowser.Konqueror]
        if sys.platform[:3] == 'win':
            graphical_browsers.append(webbrowser.WindowsDefault)
        elif sys.platform == 'darwin':
            graphical_browsers.append(webbrowser.MacOSXOSAScript)

        browser_type = None
        try:
            browser_type = type(webbrowser.get())
        except webbrowser.Error:
            pass

        if browser_type in graphical_browsers:
            printError("Unable to print qr code directly to your terminal, trying a web browser.")
            webbrowser.open('file://' + qrcode_file.name)
        else:
            printInfo("Unable to print qr code directly to your terminal, and no graphical web browser seems available.")
            printInfo("But, the qr code file is temporarily available as this file:")
            printInfo("\n    %s\n" % qrcode_file.name)
            printInfo("Alternately, if you feel like typing the seed manually into your MFA app:")
            # this is a base32-encoded binary string (for case
            # insensitivity) which is then dutifully base64-encoded by
            # amazon before putting it on the wire.  so the actual
            # secret is b32decode(b64decode(seed)), and what users
            # will need to type in to their app is just
            # b64decode(seed).  print that out so users can (if
            # desperate) type in their MFA app.
            printInfo("\n    %s\n" % base64.b64decode(seed))
    return qrcode_file

#
# Fetch the IAM user name associated with the access key in use and return the requested property
#
def fetch_from_current_user(iam_client, aws_key_id, property_name):
    try:
        # Fetch all users
        user = iam_client.get_user()['User']
        return user[property_name]
    except Exception as e:
        printException(e)

#
# Get all access keys for a given user
#
def get_all_access_keys(iam_client, user_name):
    return iam_client.list_access_keys(UserName = user_name)['AccessKeyMetadata']

#
# Get AWS account ID of authenticated user
#
def get_aws_account_id(iam_client):
    result = iam_client.list_users(MaxItems = 1)
    user_arn = result['Users'][0]['Arn']
    return user_arn.split(':')[4]

#
# Get category group name based on IAM user name
#
def get_category_group_from_user_name(user, category_groups, category_regex):
    for i, regex in enumerate(category_regex):
        if regex != None and regex.match(user):
            return category_groups[i]
    return None

#
# Initialize and compile regular expression for category groups
#
def init_iam_group_category_regex(category_groups, arg_category_regex):
    # Must have as many regex as groups
    if len(arg_category_regex) and len(category_groups) != len(arg_category_regex):
        printError('Error: you must provide as many regex as category groups.')
        return None
    else:
        category_regex = []
        for regex in arg_category_regex:
            if regex != '':
                category_regex.append(re.compile(regex))
            else:
                category_regex.append(None)
        return category_regex

#
# List an IAM user's access keys
#
def list_access_keys(iam_client, user_name):
    keys = handle_truncated_responses(iam_client.list_access_keys, {'UserName':user_name, 'MaxItems': 1}, 'AccessKeyMetadata')
    printInfo('User \'%s\' currently has %s access keys:' % (user_name, len(keys)))
    for key in keys:
        printInfo('\t%s (%s)' % (key['AccessKeyId'], key['Status']))
