# -*- coding: utf-8 -*-

import os
import shutil

from opinel.utils.profiles import *
from opinel.utils.console import configPrintException, printDebug

class TestOpinelUtilsAWSProfiles(object):

    def setup(self):
        configPrintException(True)
        self.tmp_aws_dir = '%s-opineltest' % aws_dir
        if os.path.isdir(aws_dir):
            os.rename(aws_dir, self.tmp_aws_dir)
        os.mkdir(aws_dir)
        shutil.copyfile('tests/data/config', os.path.join(aws_dir, 'config'))
        shutil.copyfile('tests/data/credentials', os.path.join(aws_dir, 'credentials'))


    def teardown(self):
        shutil.rmtree(aws_dir)
        if os.path.isdir(self.tmp_aws_dir):
            os.rename(self.tmp_aws_dir, aws_dir)


    def test_list(self):
        profiles = sorted(set(AWSProfiles.list()))
        printDebug(str(profiles))
        testprofiles = sorted(set(['l01cd3v-1', 'l01cd3v-2', 'l01cd3v-role1', 'l01cd3v-role2', 'l01cd3v-role3', 'l01cd3v-role4', 'l01cd3v-3', 'l01cd3v-4', 'testprofile', 'scout2fortravis', 'scout2fortraviswithexternalid']))
        printDebug(str(testprofiles))
        assert (testprofiles == profiles)
        profiles = AWSProfiles.list(names = 'l01cd3v-role.*')
        printDebug(str(profiles))
        assert(set(['l01cd3v-role1', 'l01cd3v-role2', 'l01cd3v-role3', 'l01cd3v-role4']) == set(profiles))
        profiles = AWSProfiles.list(names = '.*1')
        assert(set(['l01cd3v-1', 'l01cd3v-role1']) == set(profiles))


    def test_get(self):
        profile = AWSProfiles.get('l01cd3v-role1')[0]
        assert('role_arn' in profile.attributes)
        assert('source_profile' in profile.attributes)
        assert(profile.attributes['role_arn'] == 'arn:aws:iam::123456789012:role/Role1')
        assert(profile.attributes['source_profile'] == 'l01cd3v-1')


    def test_get_credentials(self):
        profile = AWSProfiles.get('l01cd3v-1')[0]
        credentials = profile.get_credentials()
        assert(credentials['SerialNumber'] ==  'arn:aws:iam::123456789111:mfa/l01cd3v')
        assert(credentials['SecretAccessKey'] == 'deadbeefdeadbeefdeadbeefdeadbeef11111111')
        assert(credentials['AccessKeyId'] == 'AKIAXXXXXXXXXXXXXXX1')

    def test_write(self):
        profile = AWSProfile(name = 'l01cd3v-role3')
        profile.set_attribute('role_arn', 'arn:aws:iam::123456789012:role/Role3')
        profile.set_attribute('source_profile', 'l01cd3v-3')
        profile.write()
        profile = AWSProfile(name = 'l01cd3v-role4')
        profile.set_attribute('role_arn', 'arn:aws:iam::123456789012:role/Role4')
        profile.set_attribute('source_profile', 'l01cd3v-4')
        profile.write()
        profile = AWSProfile(name = 'l01cd3v-5')
        profile.set_attribute('aws_access_key_id', 'AKIAXXXXXXXXXXXXXXX5')
        profile.set_attribute('aws_secret_access_key', 'deadbeefdeadbeefdeadbeefdeadbeef55555555')
        profile.write()
        profile = AWSProfile(name = 'l01cd3v-2')
        profile.set_attribute('aws_mfa_serial', 'arn:aws:iam::123456789222:mfa/l01cd3v-2')
        profile.write()
