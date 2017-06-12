# -*- coding: utf-8 -*-

from opinel.utils.aws import *
from opinel.utils.credentials import read_creds, read_creds_from_environment_variables


class TestOpinelAWS:

    def setup(self):
        self.creds = read_creds_from_environment_variables()
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
        client = connect_service('iam', self.creds)
        client = connect_service('iam', self.creds, config={})
        client = connect_service('iam', self.creds, silent=True)
        client = connect_service('ec2', self.creds, 'us-east-1')
        try:
            client = connect_service('opinelunittest', creds)
            assert(False)
        except:
            # Except an exception if invalid service name was provided
            pass


    def test_get_aws_account_id(self):
        account_id = get_aws_account_id(self.creds)
        assert (account_id == '179374595322')


    def test_get_caller_identity(self):
        result = {
            "Account": "179374595322",
            "UserId": [ "AIDAISSRBZ2MQ4EEY25GM", "AIDAJ3IA46RH552IUMC6Q" ],
            "Arn": [ "arn:aws:iam::179374595322:user/CI-local", "arn:aws:iam::179374595322:user/CI-travis" ]
        }
        identity = get_caller_identity(self.creds)
        assert (identity['Account'] == result['Account'])
        assert (identity['UserId'] in result['UserId'])
        assert (identity['Arn'] in result['Arn'])


    def test_get_name(self):
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


    def test_get_username(self):
        username = get_username(self.creds)
        assert (username == 'CI-local' or username == 'CI-travis')


    def test_handle_truncated_response(self):
        iam_client = connect_service('iam', self.creds)
        users = handle_truncated_response(iam_client.list_users, {'MaxItems': 5}, ['Users'])
