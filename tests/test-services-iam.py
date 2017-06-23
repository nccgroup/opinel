# -*- coding: utf-8 -*-

import copy
import sys
import time

from opinel.services.iam import *
from opinel.utils.aws import connect_service
from opinel.utils.console import configPrintException
from opinel.utils.credentials import read_creds, read_creds_from_environment_variables


class TestOpinelServicesIAM:

    def setup(self):
        configPrintException(True)
        self.creds = read_creds_from_environment_variables()
        if self.creds['AccessKeyId'] == None:
            self.creds = read_creds('travislike')
        self.api_client = connect_service('iam', self.creds)
        self.python = re.sub(r'\W+', '', sys.version)

    def make_username(self, username):
        return '%s-%s' % (username, self.python)


    #
    # Must be first
    #
    def test_001_create_user(self):
        user_data = create_user(self.api_client, self.make_username('OpinelUnitTest001'))
        assert len(user_data['errors']) == 0
        user_data = create_user(self.api_client, self.make_username('OpinelUnitTest001'))
        assert len(user_data['errors']) == 1
        user_data = create_user(self.api_client, self.make_username('OpinelUnitTest002'), 'BlockedUsers')
        assert len(user_data['errors']) == 0
        user_data = create_user(self.api_client, self.make_username('OpinelUnitTest003'), ['BlockedUsers', 'AllUsers'])
        assert len(user_data['errors']) == 1
        user_data = create_user(self.api_client, self.make_username('OpinelUnitTest004'), with_password = True)
        assert len(user_data['errors']) == 0
        assert 'password' in user_data
        assert len(user_data['password']) == 16
        user_data = create_user(self.api_client, self.make_username('OpinelUnitTest005'), with_password=True ,require_password_reset = True)
        assert len(user_data['errors']) == 0
        assert 'password' in user_data
        assert len(user_data['password']) == 16
        user_data = create_user(self.api_client, self.make_username('OpinelUnitTest006'), with_access_key = True)
        assert len(user_data['errors']) == 0
        assert 'AccessKeyId' in user_data
        assert user_data['AccessKeyId'].startswith('AKIA')
        assert 'SecretAccessKey' in user_data


    def test_002_add_user_to_group(self):
        create_user(self.api_client, self.make_username('OpinelUnitTest010'))
        create_user(self.api_client, self.make_username('OpinelUnitTest011'))
        add_user_to_group(self.api_client, self.make_username('OpinelUnitTest010'), 'BlockedUsers', True)
        add_user_to_group(self.api_client, self.make_username('OpinelUnitTest011'), 'BlockedUsers', False)


    def test_003_delete_virtual_mfa_device(self):
        # TODO
        pass


    def test_004_get_access_keys(self):
        create_user(self.api_client, self.make_username('OpinelUnitTest020'), with_access_key = True)
        access_keys = get_access_keys(self.api_client, self.make_username('OpinelUnitTest020'))
        assert len(access_keys) == 1


    def test_005_show_access_keys(self):
        show_access_keys(self.api_client, self.make_username('OpinelUnitTest020'))


    def test_006_init_iam_group_category_regex(self):
        pass


    #
    # Must be last
    #
    def test_999_delete_user(self):
        users = ['OpinelUnitTest001', 'OpinelUnitTest002', 'OpinelUnitTest003', 'OpinelUnitTest004', 'OpinelUnitTest005',
                 'OpinelUnitTest006',
                 'OpinelUnitTest010', 'OpinelUnitTest011',
                 'OpinelUnitTest020']
        while True:
            unmodifiable_entity = False
            remaining_users = []
            for user in users:
                errors = delete_user(self.api_client, self.make_username(user))
                if len(errors):
                    remaining_users.append(user)
                    for handled_code in ['EntityTemporarilyUnmodifiable', 'DeleteConflict']:
                        if handled_code in errors:
                            unmodifiable_entity = True
                        else:
                            printError('Failed to delete user %s' % user)
                            assert (False)
            users = copy.deepcopy(remaining_users)
            if not unmodifiable_entity:
                break
            else:
                printError('Sleeping 5 seconds before another attempt at deleting IAM users...')
                time.sleep(5)
