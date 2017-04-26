# -*- coding: utf-8 -*-

from opinel.services.cloudtrail import *
from opinel.utils.aws import connect_service
from opinel.utils.credentials import read_creds, read_creds_from_environment_variables


class TestOpinelServicesCloudtrail:

    def setup(self):
        self.creds = read_creds_from_environment_variables()
        if self.creds['AccessKeyId'] == None:
            self.creds = read_creds('travislike')
        self.api_client = connect_service('cloudtrail', self.creds, 'us-east-1')


    def test_get_trails(self):
        trails = get_trails(self.api_client)
        assert (type(trails) == list)
        trail_names = [trail['Name'] for trail in trails]
        assert ('GlobalTrail' in trail_names)
