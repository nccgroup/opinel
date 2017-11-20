# -*- coding: utf-8 -*-

from opinel.services.cloudformation import *
from opinel.utils.aws import connect_service
from opinel.utils.credentials import read_creds, read_creds_from_environment_variables


class TestOpinelServicesCloudtrail:

    def setup(self):
        self.creds = read_creds_from_environment_variables()
        if self.creds['AccessKeyId'] == None:
            self.creds = read_creds('travislike')
        self.api_client = connect_service('cloudtrail', self.creds, 'us-east-1')


    def test_create_cloudformation_resource_from_template(self):
        pass
    def test_create_stack(self):
        pass
    def test_create_or_update_stack(self):
        pass
    def test_create_stack_instances(self):
        pass
    def test_create_stack_set(self):
        pass
    def test_get_stackset_ready_accounts(self):
        pass
    def test_make_awsrecipes_stack_name(self):
        pass
    def test_prepare_cloudformation_params(self):
        pass
    def test_update_cloudformation_resource_from_template(self):
        pass
    def test_update_stack(self):
        pass
    def test_update_stack_set(self):
        pass

