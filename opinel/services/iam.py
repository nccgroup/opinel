# -*- coding: utf-8 -*-

import re

from opinel.utils.aws import handle_truncated_response
from opinel.utils.credentials import generate_password
from opinel.utils.console import printInfo, printError, printException



def add_user_to_group(iam_client, user, group, quiet = False):
    """
    Add an IAM user to an IAM group

    :param iam_client:
    :param group:
    :param user:
    :param user_info:
    :param dry_run:
    :return:
    """
    if not quiet:
        printInfo('Adding user to group %s...' % group)
    iam_client.add_user_to_group(GroupName = group, UserName = user)


def create_user(iam_client, user, groups = [], with_password= False, with_mfa = False, with_access_key = False, require_password_reset = True):
    """

    :param iam_client:                  AWS API client for IAM
    :param user:                        Name of the user to create
    :param groups:                      Name of the IAM groups to add the user to
    :param with_password:               Boolean indicating whether creation of a password should be done
    :param with_mfa:                    Boolean indicating whether creation of an MFA device should be done
    :param with_access_key:             Boolean indicating whether creation of an API access key should be done
    :param require_password_reset:      Boolean indicating whether users should reset their password after first login
    :return:
    """
    user_data = {'username': user, 'errors': []}
    printInfo('Creating user %s...' % user)
    try:
        iam_client.create_user(UserName = user)
    except Exception as e:
        user_data['errors'].append('iam:createuser')
        return user_data
    # Add user to groups
    if type(groups) != list:
        groups = [ groups ]
    for group in groups:
        try:
            add_user_to_group(iam_client, user, group)
        except Exception as e:
            printException(e)
            user_data['errors'].append('iam:addusertogroup - %s' % group)
    # Generate password
    if with_password:
        try:
            printInfo('Creating a login profile...')
            user_data['password'] = generate_password()
            iam_client.create_login_profile(UserName = user, Password = user_data['password'] , PasswordResetRequired = require_password_reset)
        except Exception as e:
            printException(e)
            user_data['errors'].append('iam:createloginprofile')
    # Enable MFA
    if False and with_mfa:
        printInfo('Enabling MFA...')
        serial = ''
        mfa_code1 = ''
        mfa_code2 = ''
        # Create an MFA device, Display the QR Code, and activate the MFA device
        try:
            mfa_serial = False # enable_mfa(iam_client, user, '%s/qrcode.png' % user)
        except Exception as e:
            return 42
    # Request access key
    if with_access_key:
        try:
            printInfo('Creating an API access key...')
            access_key = iam_client.create_access_key(UserName=user)['AccessKey']
            user_data['AccessKeyId'] = access_key['AccessKeyId']
            user_data['SecretAccessKey'] = access_key['SecretAccessKey']
        except Exception as e:
            printException(e)
            user_data['errors'].append('iam:createaccesskey')
    return user_data


def delete_user(iam_client, user, mfa_serial = None, keep_user = False, terminated_groups = []):
    """
    Delete IAM user

    :param iam_client:
    :param user:
    :param mfa_serial:
    :param keep_user:
    :param terminated_groups:
    :return:
    """
    errors = []
    printInfo('Deleting user %s...' % user)
    # Delete access keys
    try:
        aws_keys = get_access_keys(iam_client, user)
        for aws_key in aws_keys:
            try:
                printInfo('Deleting access key ID %s... ' % aws_key['AccessKeyId'], False)
                iam_client.delete_access_key(AccessKeyId = aws_key['AccessKeyId'], UserName = user)
                printInfo('Success')
            except Exception as e:
                printInfo('Failed')
                printException(e)
                errors.append(e.response['Error']['Code'])
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
                errors.append(e.response['Error']['Code'])
            delete_virtual_mfa_device(iam_client, serial)
        if mfa_serial:
            delete_virtual_mfa_device(iam_client, mfa_serial)
    except Exception as e:
        printException(e)
        printError('Faile to fetch/delete MFA device serial number for user %s.' % user)
        errors.append(e.response['Error']['Code'])
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
                errors.append(e.response['Error']['Code'])
    except Exception as e:
        printException(e)
        printError('Failed to fetch IAM groups for user %s.' % user)
        errors.append(e.response['Error']['Code'])
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
        errors.append(e.response['Error']['Code'])
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
        errors.append(e.response['Error']['Code'])
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
        errors.append(e.response['Error']['Code'])
    # Delete IAM user
    try:
        if not keep_user:
            iam_client.delete_user(UserName = user)
            printInfo('User %s deleted.' % user)
        else:
            for group in terminated_groups:
                add_user_to_group(iam_client, group, user)
    except Exception as e:
        printException(e)
        printError('Failed to delete user.')
        errors.append(e.response['Error']['Code'])
        pass
    return errors


def delete_virtual_mfa_device(iam_client, mfa_serial):
    """
    Delete a vritual MFA device given its serial number

    :param iam_client:
    :param mfa_serial:
    :return:
    """
    try:
        printInfo('Deleting MFA device %s...' % mfa_serial)
        iam_client.delete_virtual_mfa_device(SerialNumber = mfa_serial)
    except Exception as e:
        printException(e)
        printError('Failed to delete MFA device %s' % mfa_serial)
        pass

def get_access_keys(iam_client, user_name):
    """

    :param iam_client:
    :param user_name:
    :return:
    """
    keys = handle_truncated_response(iam_client.list_access_keys, {'UserName': user_name}, ['AccessKeyMetadata'])['AccessKeyMetadata']
    return keys


def show_access_keys(iam_client, user_name):
    """

    :param iam_client:
    :param user_name:
    :return:
    """
    keys = get_access_keys(iam_client, user_name)
    printInfo('User \'%s\' currently has %s access keys:' % (user_name, len(keys)))
    for key in keys:
        printInfo('\t%s (%s)' % (key['AccessKeyId'], key['Status']))


def init_iam_group_category_regex(category_groups, arg_category_regex):
    """
    Initialize and compile regular expression for category groups

    :param category_groups:
    :param arg_category_regex:
    :return:
    """
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
