#!/usr/bin/env python2

# Import AWS utils
from AWSUtils.utils import *

# Import third-party packages
import boto
import fileinput
import os
import re
import shutil


########################################
##### Helpers
########################################

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
# Fetch the IAM user name associated with the access key in use
#
def fetch_current_user_name(iam_connection, aws_key_id):
    user_name = None
    try:
        # Fetch all users
        users = handle_truncated_responses(iam_connection.get_all_users, None, ['list_users_response', 'list_users_result'], 'users')
        for user in users:
            keys = handle_truncated_responses(iam_connection.get_all_access_keys, user['user_name'], ['list_access_keys_response', 'list_access_keys_result'], 'access_key_metadata')
            for key in keys:
                if key['access_key_id'] == aws_key_id:
                    user_name = user['user_name']
                    break
            if user_name:
                break
        print 'Active user name is %s' % user_name
    except Exception, e:
        printException(e)
    return user_name

#
# Get all access keys for a given user
#
def get_all_access_keys(iam_connection, user_name):
    access_keys = iam_connection.get_all_access_keys(user_name)
    return access_keys.list_access_keys_response.list_access_keys_result.access_key_metadata

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
# List an IAM user's access keys
#
def list_access_keys(iam_connection, user_name):
    keys = handle_truncated_responses(iam_connection.get_all_access_keys, user_name, ['list_access_keys_response', 'list_access_keys_result'], 'access_key_metadata')
    print 'User \'%s\' currently has %s access keys:' % (user_name, len(keys))
    for key in keys:
        print '\t%s (%s)' % (key['access_key_id'], key['status'])
