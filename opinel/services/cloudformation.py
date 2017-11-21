# -*- coding: utf-8 -*-

import json
import os
import re

from opinel.utils.aws import connect_service, handle_truncated_response
from opinel.utils.console import printDebug, printInfo, printError, printException, prompt_4_yes_no
from opinel.utils.fs import read_file
from opinel.utils.globals import snake_to_camel

re_iam_capability = re.compile('.*?AWS::IAM.*?', re.DOTALL | re.MULTILINE)

def create_cloudformation_resource_from_template(api_client, resource_type, name, template_path, template_parameters=[], tags=[], quiet=False, need_on_failure=False):
    """
    
    :param callback:
    :param name:
    :param template_path:
    :param template_parameters:
    :param quiet:
    :return:
    """
    create = getattr(api_client, 'create_%s' % resource_type)
    resource_type = snake_to_camel(resource_type)
    params = prepare_cloudformation_params(name, template_path, template_parameters, resource_type, tags)
    if not quiet:
        printInfo('Creating the %s...' % resource_type)
    response = create(**params)
    resource_id = response['%sId' % resource_type]
    if not quiet:
        printInfo(' Success !')
    return resource_id


def create_stack(api_client, stack_name, template_path, template_parameters=[], tags=[], quiet=False):
    """
    
    :param api_client:
    :param stack_name:
    :param template_path:
    :param template_parameters:         List of parameter keys and values
    :param quiet:
    :return:
    """
    return create_cloudformation_resource_from_template(api_client, 'stack', stack_name, template_path, template_parameters, tags, quiet, need_on_failure=True)


def create_or_update_stack(api_client, stack_name, template_path, template_parameters=[], tags=[], quiet=False):
    """
    
    :param api_client:
    :param stack_name:
    :param template_path:
    :param template_parameters:         List of parameter keys and values
    :param quiet:
    :return:
    """
    try:
        return create_stack(api_client, stack_name, template_path, template_parameters, tags, quiet)
    except Exception as e:
        if type(e.response) == dict and hasattr(e, 'response') and 'Error' in e.response and e.response['Error']['Code'] == 'AlreadyExistsException':
            printInfo('Stack already exists... ', newLine = False)
            update_stack(api_client, stack_name, template_path, template_parameters, quiet)
        else:
            printException(e)


def create_stack_set(api_client, stack_set_name, template_path, template_parameters=[], tags=[], quiet=False):
    """
    
    :param api_client:
    :param stack_set_name:
    :param template_path:
    :param template_parameters:
    :param quiet:
    :return:
    """
    return create_cloudformation_resource_from_template(api_client, 'stack_set', stack_set_name, template_path, template_parameters, tags, quiet)


def create_stack_instances(api_client, stack_set_name, account_ids, regions, quiet=False):
    """
    
    :param api_client:
    :param stack_set_name:
    :param account_ids:
    :param regions:
    :return:
    """
    operation_preferences = {'FailureTolerancePercentage': 100,
       'MaxConcurrentPercentage': 100
       }
    if not quiet:
        printInfo('Creating stack instances in %d regions and %d accounts...' % (len(regions), len(account_ids)))
        printDebug(' %s' % ', '.join(regions))
    response = api_client.create_stack_instances(StackSetName=stack_set_name, Accounts=account_ids, Regions=regions, OperationPreferences=operation_preferences)
    if not quiet:
        printInfo('Successfully started operation Id %s' % response['OperationId'])
    return response['OperationId']


def get_stackset_ready_accounts(credentials, account_ids, quiet=True):
    """
    Verify which AWS accounts have been configured for CloudFormation stack set by attempting to assume the stack set execution role
    
    :param credentials:                 AWS credentials to use when calling sts:assumerole
    :param org_account_ids:             List of AWS accounts to check for Stackset configuration
    
    :return:                            List of account IDs in which assuming the stackset execution role worked
    """
    api_client = connect_service('sts', credentials, silent=True)
    configured_account_ids = []
    for account_id in account_ids:
        try:
            role_arn = 'arn:aws:iam::%s:role/AWSCloudFormationStackSetExecutionRole' % account_id
            api_client.assume_role(RoleArn=role_arn, RoleSessionName='opinel-get_stackset_ready_accounts')
            configured_account_ids.append(account_id)
        except Exception as e:
            pass

    if len(configured_account_ids) != len(account_ids) and not quiet:
        printInfo('Only %d of these accounts have the necessary stack set execution role:' % len(configured_account_ids))
        printDebug(str(configured_account_ids))
    return configured_account_ids


def make_awsrecipes_stack_name(template_path):
    """
    
    :param template_path:
    :return:
    """
    return make_prefixed_stack_name('AWSRecipes', template_path)


def make_opinel_stack_name(template_path):
    """

    :param template_path:"
    :return:
    """
    return make_prefixed_stack_name('Opinel', template_path)


def make_prefixed_stack_name(prefix, template_path):
    """

    :param prefix:
    :param template_path:
    """
    parts = os.path.basename(template_path).split('-')
    parts = parts if len(parts) == 1 else parts[:-1]
    return ('%s-%s' % (prefix, '-'.join(parts))).split('.')[0]


def prepare_cloudformation_params(stack_name, template_path, template_parameters, resource_type, tags=[], need_on_failure=False):
    """
    
    :param api_client:
    :param stack_name:
    :param template_path:
    :param template_parameters:         List of parameter keys and values
    :param quiet:
    :return:
    """
    printDebug('Reading CloudFormation template from %s' % template_path)
    template_body = read_file(template_path)
    params = {}
    params['%sName' % resource_type] = stack_name
    params['TemplateBody'] = template_body
    if len(template_parameters):
        params['Parameters'] = []
        it = iter(template_parameters)
        for param in it:
            printError('Param:: %s' % param)
            params['Parameters'].append({'ParameterKey': param,'ParameterValue': next(it)})

    if len(tags):
        params['Tags'] = tags
    if re_iam_capability.match(template_body):
        params['Capabilities'] = [
         'CAPABILITY_NAMED_IAM']
    if need_on_failure:
        params['OnFailure'] = 'ROLLBACK'
    printDebug('Stack parameters:')
    printDebug(json.dumps(params, indent=4))
    return params


def update_stack(api_client, stack_name, template_path, template_parameters=[], quiet=False):
    """
    
    :param api_client:
    :param stack_name:
    :param template_path:
    :param template_parameters:         List of parameter keys and values
    :param quiet:
    :return:
    """
    return update_cloudformation_resource_from_template(api_client, 'stack', stack_name, template_path, template_parameters, quiet = quiet)


def update_stack_set(api_client, stack_set_name, template_path, template_parameters=[], quiet=False):
    """
    
    :param api_client:
    :param stack_set_name:
    :param template_path:
    :param template_parameters:
    :param quiet:
    :return:
    """
    return update_cloudformation_resource_from_template(api_client, 'stack_set', stack_set_name, template_path, template_parameters, quiet)


def update_cloudformation_resource_from_template(api_client, resource_type, name, template_path, template_parameters=[], tags=[], quiet=False):
    """
    
    :param callback:
    :param name:
    :param template_path:
    :param template_parameters:
    :param quiet:
    :return:
    """
    try:
        update = getattr(api_client, 'update_%s' % resource_type)
        resource_type = snake_to_camel(resource_type)
        params = prepare_cloudformation_params(name, template_path, template_parameters, resource_type, tags)
        if not quiet:
            printInfo('Updating the %s...' % resource_type, newLine=False)
        response = update(**params)
        if not quiet:
            printInfo(' Success !')
        return response['OperationId']
    except Exception as e:
        if resource_type == 'Stack' and e.response['Error']['Code'] == 'ValidationError' and e.response['Error']['Message'] == 'No updates are to be performed.':
            printInfo(' Already up to date.')
        else:
            printException(e)
            printError(' Failed.')
            printDebug(e.response['Error']['Code'])
