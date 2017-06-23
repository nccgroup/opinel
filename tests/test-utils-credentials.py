# -*- coding: utf-8 -*-

import copy
import shutil
from opinel.utils.credentials import *

class TestOpinelCredentialsClass:

    def setup(self):
        self.creds = read_creds_from_environment_variables()
        if self.creds['AccessKeyId'] == None:
            self.creds = read_creds('travislike')

    def cmp(self, a, b):
        """
        Implement cmp() for Python3 tests
        """
        return (a > b) - (a < b)

    def check_credentials_dict(self, creds):
        assert 'AccessKeyId' in creds
        assert 'SecretAccessKey' in creds
        assert 'SessionToken' in creds
        assert 'Expiration' in creds
        #assert 'SerialNumber' in creds
        #assert 'TokenCode' in creds

    def check_credentials_not_empty(self, creds):
        assert (creds['AccessKeyId'].startswith('AKIA') or creds['AccessKeyId'].startswith('ASIA'))
        assert (creds['SecretAccessKey'] != None)

    def test_assume_role(self):
        creds = assume_role('Scout2', self.creds, 'arn:aws:iam::179374595322:role/Scout2', 'opinelunittesting')
        self.check_credentials_dict(creds)
        self.check_credentials_not_empty(creds)
        assert (creds['SessionToken'] != None)
        fake_creds = copy.deepcopy(self.creds)
        fake_creds['mfa_serial'] = 'arn:aws:iam::179374595322:mfa/fake'
        fake_creds['mfa_code'] = '123456'
        fake_creds['ExternalId'] = 'opinelunittesting'
        try:
            creds = assume_role('Scout2', fake_creds, 'arn:aws:iam::179374595322:role/Scout2', 'opinelunittesting')
        except Exception as e:
            pass

    def test_get_cached_credentials_filename(self):
        filename = get_cached_credentials_filename('Scout2', 'arn:aws:iam::179374595322:role/Scout2')
        assert(filename.endswith('.aws/cli/cache/Scout2--arn_aws_iam__179374595322_role-Scout2.json'))

    def test_generate_password(self):
        password = generate_password(16)
        assert len(password) == 16

    def test_init_creds(self):
        creds = init_creds()
        self.check_credentials_dict(creds)

    def test_init_sts_session(self):
        creds = init_sts_session('travislike-sts', self.creds, 900, 'opinelunittesting', False)
        self.check_credentials_dict(creds)
        fake_creds = copy.deepcopy(self.creds)
        fake_creds['SerialNumber'] = 'arn:aws:iam::179374595322:mfa/fake'
        fake_creds['TokenCode'] = '123456'
        try:
            creds = init_sts_session('travislike-sts', fake_creds, 900, 'opinelunittesting', False)
        except:
            pass


    def test_read_creds_from_aws_credentials_file(self):
        test_cases = [{'profile_name': 'l01cd3v-1','credentials_file': 'tests/data/credentials'}, {'profile_name': 'l01cd3v-2','credentials_file': 'tests/data/credentials'}, {'profile_name': 'l01cd3v-3','credentials_file': 'tests/data/credentials'}, {'profile_name': 'l01cd3v-4','credentials_file': 'tests/data/credentials'}]
        results = [
         ('AKIAXXXXXXXXXXXXXXX1', 'deadbeefdeadbeefdeadbeefdeadbeef11111111', 'arn:aws:iam::123456789111:mfa/l01cd3v',
 None),
         ('AKIAXXXXXXXXXXXXXXX2', 'deadbeefdeadbeefdeadbeefdeadbeef22222222', 'arn:aws:iam::123456789222:mfa/l01cd3v',
 None),
         ('ASIAXXXXXXXXXXXXXXX3', 'deadbeefdeadbeefdeadbeefdeadbeef33333333', None, 'deadbeef333//////////ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg==/ZGVhZGJlZWZkZWFkYmVlZg==+ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg==/ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg=='),
         ('ASIAXXXXXXXXXXXXXXX4', 'deadbeefdeadbeefdeadbeefdeadbeef44444444', None, 'deadbeef444//////////ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg==/ZGVhZGJlZWZkZWFkYmVlZg==+ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg==/ZGVhZGJlZWZkZWFkYmVlZg==ZGVhZGJlZWZkZWFkYmVlZg==')]
        for test_case, result in zip(test_cases, results):
            credentials = read_creds_from_aws_credentials_file(**test_case)
            assert credentials['AccessKeyId'] == result[0]
            assert credentials['SecretAccessKey'] == result[1]
            assert credentials['SerialNumber'] == result[2]
            assert credentials['SessionToken'] == result[3]

        return None

    def test_read_creds_from_csv(self):
        creds = read_creds_from_csv('tests/data/accessKeys1.csv')
        assert creds != None
        assert type(creds) == tuple
        assert creds[0] == 'AKIAJJ5TE81PVO72WPTQ'
        assert creds[1] == '67YkvxJ8Qx0EI97NvlIyM9kVz/uKddd0z0uGj123'
        assert creds[2] == None
        creds = read_creds_from_csv('tests/data/accessKeys2.csv')
        assert creds[0] == 'AKIAJJ5TE81PVO72WPTQ'
        assert creds[1] == '67YkvxJ8Qx0EI97NvlIyM9kVz/uKddd0z0uGj123'
        assert creds[2] == None
        creds = read_creds_from_csv('tests/data/accessKeys3.csv')
        assert creds[0] == 'AKIAJJ5TE81PVO72WPTQ'
        assert creds[1] == '67YkvxJ8Qx0EI97NvlIyM9kVz/uKddd0z0uGj123'
        assert creds[2] == 'arn:aws:iam::123456789111:mfa/l01cd3v'
        creds = read_creds_from_csv('tests/data/accessKeys4.csv')
        assert creds[0] == 'AKIAJJ5TE81PVO72WPTQ'
        assert creds[1] == '67YkvxJ8Qx0EI97NvlIyM9kVz/uKddd0z0uGj123'
        assert creds[2] == 'arn:aws:iam::123456789111:mfa/l01cd3v'
        return

    def test_read_creds_from_ec2_instance_metadata(self):
        pass

    def test_read_creds_from_environment_variables(self):
        os.environ['AWS_ACCESS_KEY_ID'] = 'environment-AKIAJJ5TE81PVO72WPTQ'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'environment-67YkvxJ8Qx0EI97NvlIyM9kVz/uKddd0z0uGj123'
        os.environ['AWS_SESSION_TOKEN'] = 'environment-session/////token'
        creds = read_creds_from_environment_variables()
        assert creds != None
        assert type(creds) == dict
        assert creds['AccessKeyId'] == 'environment-AKIAJJ5TE81PVO72WPTQ'
        assert creds['SecretAccessKey'] == 'environment-67YkvxJ8Qx0EI97NvlIyM9kVz/uKddd0z0uGj123'
        assert creds['SessionToken'] == 'environment-session/////token'
        return

    def test_read_profile_from_aws_config_file(self):
        role_arn, source_profile = read_profile_from_aws_config_file('l01cd3v-role2', config_file='tests/data/config')
        assert role_arn == 'arn:aws:iam::123456789012:role/Role2'
        assert source_profile == 'l01cd3v-2'

    def test_get_profiles_from_aws_credentials_file(self):
        profiles1 = get_profiles_from_aws_credentials_file(credentials_files=['tests/data/credentials'])
        profiles2 = sorted(['l01cd3v-1', 'l01cd3v-2', 'l01cd3v-3', 'l01cd3v-4'])
        assert profiles1 == profiles2

    def test_show_profiles_from_aws_credentials_file(self):
        show_profiles_from_aws_credentials_file(credentials_files=['tests/data/credentials'])

    def test_write_creds_to_aws_credentials_file(self):
        tmpcredentialsfile = 'tmpcredentialsfile'
        if os.path.isfile(tmpcredentialsfile):
            os.remove(tmpcredentialsfile)
            shutil.copy('tests/data/credentials', tmpcredentialsfile)
        creds = init_creds()
        creds['AccessKeyId'] = 'AKIAJJ5TE81PVO72WPTQ'
        creds['SecretAccessKey'] = '67YkvxJ8Qx0EI97NvlIyM9kVz/uKddd0z0uGj123'
        write_creds_to_aws_credentials_file('testprofile', creds, tmpcredentialsfile)
        creds['SessionToken'] = 'opineltestsessiontoken'
        creds['SerialNumber'] = 'arn:aws:iam::123456789111:mfa/l01cd3v'
        creds['Expiration'] = '2017-04-19 02:23:16+00:00'
        write_creds_to_aws_credentials_file('testprofile', creds, tmpcredentialsfile)
        write_creds_to_aws_credentials_file('testprofile', creds, tmpcredentialsfile)
        os.remove(tmpcredentialsfile)

    def test_complete_profile(self):
        pass

    def test_read_creds(self):
        creds = read_creds('travislike')
        creds = read_creds('', csv_file='tests/data/accessKeys1.csv')
