#!/usr/bin/env python2

# Import AWS utils
from AWSUtils.utils import *

# Import third-party packages
import boto
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

# Import stock packages
import base64
from collections import Counter
import fileinput
import os
import re
import shutil
import tempfile
import webbrowser


########################################
##### Helpers
########################################

#
# Add an IAM user to an IAM group and updates the user info if needed
#
def add_user_to_group(iam_connection, group, user, user_info = None, dry_run = False):
    if not dry_run:
        iam_connection.add_user_to_group(group, user)
    if user_info != None:
        user_info[user]['groups'].append(group)

#
# Add an IAM user to a category group if he doesn't belong to one already
#
def add_user_to_category_group(iam_connection, current_groups, category_groups, category_regex, user, user_info = None, dry_run = False):
        category_memberships = list((Counter(current_groups) & Counter(category_groups)).elements())
        if not len(category_memberships):
            group = None
            sys.stdout.write('User \'%s\' does not belong to any of the category group (%s). ' % (user, ', '.join(category_groups)))
            sys.stdout.flush()
            if len(category_regex):
                group = get_category_group_from_user_name(user, category_groups, category_regex)
                if not group:
                    sys.stdout.write('Failed to determine the category group based on the user name.\n')
                else:
                    sys.stdout.write('Automatically adding...\n')
                    add_user_to_group(iam_connection, group, user, user_info, dry_run)
                sys.stdout.flush()
            if not group and prompt_4_yes_no('Do you want to remediate this now'):
                group = prompt_4_value('Which category group should \'%s\' belong to' % user, choices = category_groups, display_choices = True, display_indices = True, is_question = True)
                add_user_to_group(iam_connection, group, user, user_info, dry_run)

#
# Add an IAM user to the common group(s) if he's not yet a member
#
def add_user_to_common_group(iam_connection, current_groups, common_groups, user, force_common_group, user_info = None, dry_run = False):
    mandatory_memberships = list((Counter(current_groups) & Counter(common_groups)).elements())
    for group in common_groups:
        if group not in mandatory_memberships:
            sys.stdout.write('User \'%s\' does not belong to the mandatory common group \'%s\'. ' % (user, group))
            if force_common_group == True:
                sys.stdout.write('Automatically adding...\n')
                add_user_to_group(iam_connection, group, user, user_info, dry_run)
            elif prompt_4_yes_no('Do you want to remediate this now'):
                add_user_to_group(iam_connection, group, user, user_info, dry_run)
            sys.stdout.flush()

#
# Connect to IAM
#
def connect_iam(key_id, secret, session_token):
    try:
        return boto.connect_iam(aws_access_key_id = key_id, aws_secret_access_key = secret, security_token = session_token)
    except Exception, e:
        printException(e)
        return None

#
# Create default groups
#
def create_default_groups(iam_connection, common_groups, category_groups, dry_run):
    all_groups = common_groups + category_groups
    for group in all_groups:
        try:
            print 'Creating group \'%s\'...' % group
            if not dry_run:
                iam_connection.create_group(group)
        except Exception, e:
            printException(e)
            pass

#
# Create and activate an MFA virtual device
#
def enable_mfa(iam_connection, user):
    mfa_serial = ''
    qrcode_file = None
    try:
        mfa_device = iam_connection.create_virtual_mfa_device('/', user)
        result = mfa_device['create_virtual_mfa_device_response']['create_virtual_mfa_device_result']['virtual_mfa_device']
        mfa_serial = result['serial_number']
        mfa_png = result['qr_code_png']
        mfa_seed = result['base_32_string_seed']
        qrcode_file = display_qr_code(mfa_png, mfa_seed)
        while True:
            mfa_code1 = prompt_4_mfa_code()
            mfa_code2 = prompt_4_mfa_code(activate = True)
            try:
                iam_connection.enable_mfa_device(user, mfa_serial, mfa_code1, mfa_code2)
                break
            except Exception, e:
                printException(e)
                pass
        print 'Succesfully enabled MFA for for \'%s\'. The device\'s ARN is \'%s\'.' % (user, mfa_serial)
    except Exception, e:
        printException(e)
        # We shouldn't return normally because if we've gotten here
        # the user has potentially not set up the MFA device
        # correctly, so we don't want to e.g. write the .no-mfa
        # credentials file or anything.
        raise
    finally:
        if qrcode_file is not None:
            # This is a tempfile.NamedTemporaryFile, so simply closing
            # it will also unlink it.
            qrcode_file.close()
    return mfa_serial

#
# Delete IAM user
#
def delete_user(iam_connection, user, stage = 6, serial = None):
    # Delete access keys
    if stage >= 6:
        try:
            # Get all keys
            aws_keys = get_all_access_keys(iam_connection, user)
            for aws_key in aws_keys:
                try:
                    iam_connection.delete_access_key(aws_key['access_key_id'], user)
                except Exception, e:
                    printException(e)
                    pass
        except Exception, e:
            printException(e)
            print 'Failed to delete access keys.'
            pass
    # Fetch MFA serial if needed
    if not serial and stage >= 4:
        try:
            mfa_devices = iam_connection.get_all_mfa_devices(user)
            serial = mfa_devices.list_mfa_devices_response.list_mfa_devices_result.mfa_devices[0].serial_number
        except Exception, e:
            printException(e)
            print 'Failed to fetch MFA device serial number for user %s' % user
            pass
    # Deactivate MFA device
    if stage >= 5:
        try:
            iam_connection.deactivate_mfa_device(user, serial)
        except Exception, e:
            printException(e)
            print 'Failed to deactivate MFA device.'
            pass
    # Delete MFA device
    if stage >= 4:
        try:
            # Pending merge of https://github.com/boto/boto/pull/3010
            print 'Boto does not support MFA device deletion yet. You\'ll need to run the following command:'
            print 'aws --profile %s iam delete-virtual-mfa-device --serial-number %s' % ('XXX', serial)
        except Exception, e:
            printException(e)
            pass
    # Remove IAM user from groups
    if stage >= 3:
        try:
            groups = iam_connection.get_groups_for_user(user)
            groups = groups['list_groups_for_user_response']['list_groups_for_user_result']['groups']
            for group in groups:
                iam_connection.remove_user_from_group(group['group_name'], user)
        except Exception, e:
            printException(e)
            print 'Failed to remove user from groups.'
            pass
    # Delete login profile
    if stage >= 2:
        try:
            iam_connection.delete_login_profile(user)
        except Exception, e:
            printException(e)
            print 'Failed to delete login profile.'
            pass
    # Delete IAM user
    if stage >= 1:
        try:
            iam_connection.delete_user(user)
        except Exception, e:
            printException(e)
            print 'Failed to delete user.'
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
    qrcode_file = tempfile.NamedTemporaryFile(suffix='.png', delete=True)
    qrcode_file.write(base64.b64decode(png))
    qrcode_file.flush()
    if _fabulous_available:
        fabulous.utils.term.bgcolor = 'white'
        print fabulous.image.Image(qrcode_file, 100)
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
            print "Unable to print qr code directly to your terminal, trying a web browser."
            webbrowser.open('file://' + qrcode_file.name)
        else:
            print "Unable to print qr code directly to your terminal, and no graphical web browser seems available."
            print "But, the qr code file is temporarily available as this file:"
            print "\n    %s\n" % qrcode_file.name
            print "Alternately, if you feel like typing the seed manually into your MFA app:"
            # this is a base32-encoded binary string (for case
            # insensitivity) which is then dutifully base64-encoded by
            # amazon before putting it on the wire.  so the actual
            # secret is b32decode(b64decode(seed)), and what users
            # will need to type in to their app is just
            # b64decode(seed).  print that out so users can (if
            # desperate) type in their MFA app.
            print "\n    %s\n" % base64.b64decode(seed)
    return qrcode_file

#
# Fetch the IAM user name associated with the access key in use and return the requested property
#
def fetch_from_current_user(iam_connection, aws_key_id, property_name):
    try:
        # Fetch all users
        user = iam_connection.get_user()['get_user_response']['get_user_result']['user']
        return user[property_name]
    except Exception, e:
        printException(e)

#
# Get all access keys for a given user
#
def get_all_access_keys(iam_connection, user_name):
    access_keys = iam_connection.get_all_access_keys(user_name)
    return access_keys.list_access_keys_response.list_access_keys_result.access_key_metadata

#
# Get category group name based on IAM user name
#
def get_category_group_from_user_name(user, category_groups, category_regex):
    for i, regex in enumerate(category_regex):
        if regex != None and regex.match(user):
            return category_groups[i]
    return None

#
# Handle truncated responses
#
def handle_truncated_responses(callback, callback_args, result_path, items_name):
    marker_value = None
    items = []
    while True:
        if callback_args:
            result = callback(callback_args, marker = marker_value)
        else:
            result = callback(marker = marker_value)
        for key in result_path:
            result = result[key]
        marker_value = result['marker'] if result['is_truncated'] != 'false' else None
        items = items + result[items_name]
        if marker_value is None:
            break
    return items

#
# Initialize and compile regular expression for category groups
#
def init_iam_group_category_regex(category_groups, arg_category_regex):
    # Must have as many regex as groups
    if len(arg_category_regex) and len(category_groups) != len(arg_category_regex):
        print 'Error: you must provide as many regex as category groups.'
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
def list_access_keys(iam_connection, user_name):
    keys = handle_truncated_responses(iam_connection.get_all_access_keys, user_name, ['list_access_keys_response', 'list_access_keys_result'], 'access_key_metadata')
    print 'User \'%s\' currently has %s access keys:' % (user_name, len(keys))
    for key in keys:
        print '\t%s (%s)' % (key['access_key_id'], key['status'])
