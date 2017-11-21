# -*- coding: utf-8 -*-

from opinel.services.cloudtrail import *
from opinel.utils.aws import connect_service
from opinel.utils.console import configPrintException, printError, printException, printInfo
from opinel.utils.credentials import read_creds, read_creds_from_environment_variables

from opinel.services.organizations import *

class TestOpinelServicesOrganizations:

    def setup(self):
        configPrintException(True)
        self.creds = read_creds_from_environment_variables()
        if self.creds['AccessKeyId'] == None:
            self.creds = read_creds('travislike')
        self.api_client = connect_service('organizations', self.creds, 'us-east-1')


    def test_get_children_organizational_units(self):
        try:
            get_children_organizational_units(self.api_client, [{'Id': 'r-1234'}])
        except Exception as e:
            assert (e.response['Error']['Code'] == 'AccessDeniedException')

    def test_get_organization_account_ids(self):
        try:
            get_organization_account_ids(self.api_client)
        except Exception as e:
            assert (e.response['Error']['Code'] == 'AccessDeniedException')

    def test_get_organization_accounts(self):
        try:
            get_organization_accounts(self.api_client)
        except Exception as e:
            assert (e.response['Error']['Code'] == 'AccessDeniedException')

    def test_get_organizational_units(self):
        try:
            get_organizational_units(self.api_client)
        except Exception as e:
            assert (e.response['Error']['Code'] == 'AccessDeniedException')

    def test_list_accounts_for_parent(self):
        try:
            list_accounts_for_parent(self.api_client, {'Id': 'r-1234'})
        except Exception as e:
            assert (e.response['Error']['Code'] == 'AccessDeniedException')

