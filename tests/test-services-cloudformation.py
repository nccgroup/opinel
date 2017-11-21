# -*- coding: utf-8 -*-

import binascii
import os
import sys
import time

from opinel.services.cloudformation import *
from opinel.utils.aws import connect_service
from opinel.utils.console import configPrintException
from opinel.utils.credentials import read_creds, read_creds_from_environment_variables


class TestOpinelServicesCloudformation:

    def setup(self):
        configPrintException(True)
        self.creds = read_creds_from_environment_variables()
        if self.creds['AccessKeyId'] == None:
            self.creds = read_creds('travislike')
        self.api_client = connect_service('cloudformation', self.creds, 'us-east-1')
        self.python = re.sub(r'\W+', '', sys.version)
        self.cleanup = {'stacks': []}


    def make_travisname(self, testname):
        return '%s-%s-%s' % (testname, binascii.b2a_hex(os.urandom(4)).decode('utf-8'), self.python)


    def test_create_cloudformation_resource_from_template(self):
        # Tested by other functions...
        pass

    def test_create_stack(self):
        #create_stack(api_client, stack_name, template_path, template_parameters=[], tags=[], quiet=False)
        stack_name = self.make_travisname('OpinelUnitTestStack001')
        create_stack(self.api_client, stack_name, 'tests/data/cloudformation-001.json')
        self.cleanup['stacks'].append(stack_name)
        try:
            tags = [ {'Key': 'Opinel', 'Value': 'Opinel'} ]
            create_stack(self.api_client, stack_name, 'tests/data/cloudformation-001.json', tags = tags)
        except:
            pass
        stack_name = self.make_travisname('OpinelUnitTestStack002')
        params = [ 'Param002', 'l01cd3v' ]
        create_stack(self.api_client, stack_name, 'tests/data/cloudformation-002.json', params)
        self.cleanup['stacks'].append(stack_name)


    def test_create_or_update_stack(self):
        stack_name = self.make_travisname('OpinelUnitTestStack003')
        create_or_update_stack(self.api_client, stack_name, 'tests/data/cloudformation-003.json')
        timer = 0
        while True:
            printError('Checking the stack\'s status...')
            time.sleep(5)
            timer += 5
            stack_info = self.api_client.describe_stacks(StackName = stack_name)
            if timer > 120 or stack_info['Stacks'][0]['StackStatus'] != 'CREATE_IN_PROGRESS':
                break
        printError('Ready for update !')
        create_or_update_stack(self.api_client, stack_name, 'tests/data/cloudformation-003.json')
        self.cleanup['stacks'].append(stack_name)


    def test_create_stack_instances(self):
        pass
    def test_create_stack_set(self):
        pass
    def test_get_stackset_ready_accounts(self):
        pass


    def test_make_awsrecipes_stack_name(self):
        assert (make_awsrecipes_stack_name('/home/l01cd3v/test.json') == 'AWSRecipes-test')


    def make_opinel_stack_name(self):
        assert (make_opinel_stack_name('/home/l01cd3v/test.json') == 'Opinel-test')


    def make_prefixed_stack_name(self):
        assert (make_prefixed_stack_name('test', '/home/l01cd3v/test.json') == 'test-test')
        assert (make_prefixed_stack_name('test', 'C:\Users\l01cd3v\test.json') == 'test-test')
        assert (make_prefixed_stack_name('test', 'test') == 'test-test')


    def test_prepare_cloudformation_params(self):
        # Should be tested by other calls
        pass


    def test_update_cloudformation_resource_from_template(self):
        pass


    def test_update_stack(self):
        pass
    def test_update_stack_set(self):
        pass


    def teardown(self):
        if len(self.cleanup['stacks']):
            for stack_name in self.cleanup['stacks']:
                self.api_client.delete_stack(StackName = stack_name)

