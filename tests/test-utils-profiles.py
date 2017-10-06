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
        profiles = AWSProfiles.list()
        assert(set(['l01cd3v-1', 'l01cd3v-2', 'l01cd3v-role1', 'l01cd3v-role2', 'l01cd3v-3', 'l01cd3v-4']) == set(profiles))
        profiles = AWSProfiles.list(filters = 'l01cd3v-role.*')
        printDebug(str(profiles))
        assert(set(['l01cd3v-role1', 'l01cd3v-role2']) == set(profiles))
        profiles = AWSProfiles.list(filters = '.*1')
        assert(set(['l01cd3v-1', 'l01cd3v-role1']) == set(profiles))


    def test_get(self):
        profile = AWSProfiles.get('l01cd3v-role1')[0]
        assert(hasattr(profile, 'role_arn'))
        assert(hasattr(profile, 'source_profile'))
        assert(getattr(profile, 'role_arn') == 'arn:aws:iam::123456789012:role/Role1')
        assert(getattr(profile, 'source_profile') == 'l01cd3v-1')


    def test_get_credentials(self):
        profile = AWSProfiles.get('l01cd3v-1')[0]
        credentials = profile.get_credentials()
        assert(credentials['SerialNumber'] ==  'arn:aws:iam::123456789111:mfa/l01cd3v')
        assert(credentials['SecretAccessKey'] == 'deadbeefdeadbeefdeadbeefdeadbeef11111111')
        assert(credentials['AccessKeyId'] == 'AKIAXXXXXXXXXXXXXXX1')

