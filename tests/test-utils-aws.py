# -*- coding: utf-8 -*-

from opinel.utils.aws import *
from opinel.utils.credentials import read_creds, read_creds_from_ec2_instance_metadata


class TestOpinelAWS:

    def setup(self):
        self.creds = read_creds_from_ec2_instance_metadata()
        if self.creds['AccessKeyId'] == None:
            self.creds = read_creds('travislike')

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
#        creds = read_creds('travislike')
        client = connect_service('iam', self.creds)
        client = connect_service('iam', self.creds, config={})
        client = connect_service('iam', self.creds, silent=True)
        client = connect_service('ec2', self.creds, 'us-east-1')
        try:
            client = connect_service('opinelunittest', creds)
        except:
            pass

    def test_get_name(selfs):
        pass
        #get_name(src, dst, default_attribute):
        src1 = {'Id': 'IdValue'}
        src2 = {'Tags': [{'Key': 'Foo', 'Value': 'Bar'}, {'Key': 'Name', 'Value': 'TaggedName'}, {'Key': 'Opinel', 'Value': 'UnitTest'}], 'Id': 'IdValue'}
        src3 = {'Tags': [{'Key': 'Foo', 'Value': 'Bar'}, {'Key': 'Fake', 'Value': 'TaggedName'}, {'Key': 'Opinel', 'Value': 'UnitTest'}], 'Id': 'IdValue'}
        name = get_name(src1, {}, 'Id')
        assert (name == 'IdValue')
        name = get_name(src2, {}, 'Id')
        assert (name == 'TaggedName')
        name = get_name(src3, {}, 'Id')
        assert (name == 'IdValue')


    def test_handle_truncated_response(self):
#        creds = read_creds('travislike')
        iam_client = connect_service('iam', self.creds)
        users = handle_truncated_response(iam_client.list_users, {'MaxItems': 5}, ['Users'])
