# -*- coding: utf-8 -*-

from opinel.utils.aws import *
from opinel.utils.credentials import read_creds


class TestOpinelAWS:

    def test_build_region_list(self):
        assert type(build_region_list('ec2', [])) == list
        assert type(build_region_list('ec2', [], 'aws-us-gov')) == list
        assert 'cn-north-1' in build_region_list('ec2', [], 'aws-cn')
        assert 'cn-north-1' not in build_region_list('ec2')
        assert 'us-gov-west-1' in build_region_list('ec2', [], 'aws-us-gov')
        assert 'us-gov-west-1' not in build_region_list('ec2')
        assert ['us-east-1'] == build_region_list('ec2', ['us-east-1'])
        assert 'us-west-2' in build_region_list('ec2', ['us-east-1', 'us-east-2', 'us-west-2'])
        assert 'us-east-1' not in build_region_list('ec2', ['us-west-1'])
        assert 'us-east-1' not in build_region_list('ec2', ['us-east-1', 'us-east-2'], 'aws-cn')
        assert build_region_list('') == []


    def test_connect_service(self):
        creds = read_creds('travislike')
        client = connect_service('iam', creds)
        client = connect_service('iam', creds, config={})
        client = connect_service('iam', creds, silent=True)
        client = connect_service('ec2', creds, 'us-east-1')
        try:
            client = connect_service('opinelunittest', creds)
        except:
            pass


    def test_handle_truncated_response(self):
        creds = read_creds('travislike')
        iam_client = connect_service('iam', creds)
        users = handle_truncated_response(iam_client.list_users, {'MaxItems': 5}, ['Users'])
