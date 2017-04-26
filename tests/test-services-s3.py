# -*- coding: utf-8 -*-

from opinel.services.s3 import *
from opinel.utils.aws import connect_service
from opinel.utils.credentials import read_creds, read_creds_from_environment_variables


class TestOpinelServicesS3:

    def setup(self):
        self.creds = read_creds_from_environment_variables()
        if self.creds['AccessKeyId'] == None:
            self.creds = read_creds('travislike')
        self.api_client = connect_service('s3', self.creds, 'us-east-1')


    def test_get_s3_bucket_location(self):
        location = get_s3_bucket_location(self.api_client, 'l01cd3v-scout2-region-sa-east-1')
        assert (location == 'sa-east-1')
        location = get_s3_bucket_location(self.api_client, 'l01cd3v-scout2-region-us-east-1')
        assert (location == 'us-east-1')
        location = get_s3_bucket_location(self.api_client, 'l01cd3v-scout2-region-eu-central-1')
        assert (location == 'eu-central-1')
