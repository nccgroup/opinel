# -*- coding: utf-8 -*-

from opinel.services.cloudtrail import *
from opinel.utils.aws import connect_service
from opinel.utils.console import configPrintException, printError, printException, printInfo
from opinel.utils.credentials import read_creds, read_creds_from_environment_variables, assume_role

from opinel.services.organizations import *

class TestOpinelServicesOrganizations:

    def setup(self):
        configPrintException(True)
        self.creds = read_creds_from_environment_variables()
        if self.creds['AccessKeyId'] == None:
            self.creds = read_creds('travislike')
        self.org_creds = assume_role('OpinelUnitTest', self.creds,'arn:aws:iam::990492604467:role/OpinelUnitTest', 'opinelunittesting')
        self.badapi_client = connect_service('organizations', self.creds, 'us-east-1')
        self.api_client = connect_service('organizations', self.org_creds, 'us-east-1')


    def test_get_children_organizational_units(self):
        try:
            get_children_organizational_units(self.badapi_client, [{'Id': 'r-6qnh'}])
        except Exception as e:
            assert (e.response['Error']['Code'] == 'AccessDeniedException')
        ous = get_children_organizational_units(self.api_client, [{'Id': 'r-6qnh'}])
        self.check_ous(ous)


    def test_get_organization_account_ids(self):
        try:
            get_organization_account_ids(self.badapi_client)
        except Exception as e:
            assert (e.response['Error']['Code'] == 'AccessDeniedException')
        assert ('990492604467' in get_organization_account_ids(self.api_client))


    def test_get_organization_accounts(self):
        try:
            get_organization_accounts(self.badapi_client)
        except Exception as e:
            assert (e.response['Error']['Code'] == 'AccessDeniedException')
        accounts = get_organization_accounts(self.api_client)
        self.check_accounts(accounts)


    def test_get_organizational_units(self):
        try:
            get_organizational_units(self.badapi_client)
        except Exception as e:
            assert (e.response['Error']['Code'] == 'AccessDeniedException')
        ous = get_organizational_units(self.api_client)
        self.check_ous(ous)


    def test_list_accounts_for_parent(self):
        try:
            list_accounts_for_parent(self.badapi_client, {'Id': 'r-6qnh'})
        except Exception as e:
            assert (e.response['Error']['Code'] == 'AccessDeniedException')
        accounts = list_accounts_for_parent(self.api_client, {'Id': 'r-6qnh'})
        self.check_accounts(accounts)


    def check_accounts(self, accounts):
        root_found = False
        for account in accounts:
            if account['Id'] == '990492604467':
                root_found = True
                break
        assert (root_found)

    def check_ous(self, ous):
        ou_found = False
        for ou in ous:
            if ou['Id'] == 'r-6qnh':
                ou_found = True
                break
        assert (ou_found)
