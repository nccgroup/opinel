# -*- coding: utf-8 -*-

import binascii
import copy
import os
import sys
import time

from opinel.services.iam import *
from opinel.utils.aws import connect_service
from opinel.utils.console import configPrintException, printDebug
from opinel.utils.credentials import read_creds, read_creds_from_environment_variables


class TestOpinelServicesIAM:

    def setup(self):
        configPrintException(True)
        self.creds = read_creds_from_environment_variables()
        if self.creds['AccessKeyId'] == None:
            self.creds = read_creds('travislike')
        self.api_client = connect_service('iam', self.creds)
        self.python = re.sub(r'\W+', '', sys.version)
        self.cleanup = {'groups': [], 'users': []}


    def make_travisname(self, testname):
        return '%s-%s-%s' % (testname, binascii.b2a_hex(os.urandom(4)).decode('utf-8'), self.python)


    def assert_group_create(self, groups_data, error_count):
        for group_data in groups_data:
            self.assert_create('groups', group_data, error_count)


    def assert_user_create(self, user_data, error_count):
        self.assert_create('users', user_data, error_count)


    def assert_create(self, resource_type, resource_data, error_count):
        assert len(resource_data['errors']) == error_count
        nameattr = '%sname' % resource_type[:-1]
        if error_count == 0:
            printDebug('Successfully created %s %s' % (resource_type[:-1], resource_data[nameattr]))
            self.cleanup[resource_type].append(resource_data[nameattr])


    def test_create_user(self):
        user_data = create_user(self.api_client, self.make_travisname('OpinelUnitTest001'))
        self.assert_user_create(user_data, 0)
        user_data = create_user(self.api_client, self.cleanup['users'][0])
        self.assert_user_create(user_data, 1)
        user_data = create_user(self.api_client, self.make_travisname('OpinelUnitTest002'), 'BlockedUsers')
        self.assert_user_create(user_data, 0)
        user_data = create_user(self.api_client, self.make_travisname('OpinelUnitTest003'), ['BlockedUsers', 'AllUsers'])
        self.assert_user_create(user_data, 1)
        user_data = create_user(self.api_client, self.make_travisname('OpinelUnitTest004'), with_password = True)
        self.assert_user_create(user_data, 0)
        assert 'password' in user_data
        assert len(user_data['password']) == 16
        user_data = create_user(self.api_client, self.make_travisname('OpinelUnitTest005'), with_password=True ,require_password_reset = True)
        self.assert_user_create(user_data, 0)
        assert 'password' in user_data
        assert len(user_data['password']) == 16
        user_data = create_user(self.api_client, self.make_travisname('OpinelUnitTest006'), with_access_key = True)
        self.assert_user_create(user_data, 0)
        assert 'AccessKeyId' in user_data
        assert user_data['AccessKeyId'].startswith('AKIA')
        assert 'SecretAccessKey' in user_data


    def test_delete_user(self):
        # Tested as part of teardown
        pass


    def test_add_user_to_group(self):
        user010 = create_user(self.api_client, self.make_travisname('OpinelUnitTest010'))
        self.assert_user_create(user010, 0)
        user011 = create_user(self.api_client, self.make_travisname('OpinelUnitTest011'))
        self.assert_user_create(user011, 0)
        add_user_to_group(self.api_client, user010['username'], 'BlockedUsers', True)
        add_user_to_group(self.api_client, user011['username'], 'BlockedUsers', False)


    def test_delete_virtual_mfa_device(self):
        # TODO
        pass


    def test_get_access_keys(self):
        user020 = create_user(self.api_client, self.make_travisname('OpinelUnitTest020'), with_access_key = True)
        self.assert_user_create(user020, 0)
        access_keys = get_access_keys(self.api_client, self.cleanup['users'][0])
        assert len(access_keys) == 1


    def test_show_access_keys(self):
        user021 = create_user(self.api_client, self.make_travisname('OpinelUnitTest021'), with_access_key = True)
        self.assert_user_create(user021, 0)
        show_access_keys(self.api_client, self.cleanup['users'][0])


    def test_init_group_category_regex(self):
        init_group_category_regex(['a', 'b'], ['', '.*hello.*'])
        pass


    def test_create_groups(self):
        group001 = self.make_travisname('OpinelUnitTest001')
        groups = create_groups(self.api_client, group001)
        self.assert_group_create(groups, 0)
        group002 = self.make_travisname('OpinelUnitTest002')
        group003 = self.make_travisname('OpinelUnitTest003')
        groups = create_groups(self.api_client, [ group002, group003 ])
        self.assert_group_create(groups, 0)
        group004 = self.make_travisname('HelloWorld')
        groups = create_groups(self.api_client, group004)
        self.assert_group_create(groups, 1)


    def teardown(self):
        if len(self.cleanup['users']):
            self.delete_resources('users')
        if len(self.cleanup['groups']):
            self.delete_resources('groups')


    def delete_resources(self, resource_type):
        resources = copy.deepcopy(self.cleanup[resource_type])
        while True:
            unmodifiable_resource = False
            remaining_resources = []
            printDebug('Attempting to delete the following %s: %s' % (resource_type, str(resources))            )
            time.sleep(5)
            for resource in resources:
                if resource_type == 'groups':
                    errors = []
                    try:
                        self.api_client.delete_group(GroupName = resource)
                    except:
                        errors = [ 'EntityTemporarilyUnmodifiable' ]
                else:
                    method = globals()['delete_%s' % resource_type[:-1]]
                    errors = method(self.api_client, resource)
                if len(errors):
                    printDebug('Errors when deleting %s' % resource)
                    remaining_resources.append(resource)
                    for handled_code in ['EntityTemporarilyUnmodifiable', 'DeleteConflict']:
                        if handled_code in errors:
                            unmodifiable_resource = True
                        else:
                            printError('Failed to delete %s %s' % (resource_type[:-1], resource))
                            assert (False)
            resources = copy.deepcopy(remaining_resources)
            if not unmodifiable_resource:
                break

