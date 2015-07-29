#!/usr/bin/env python2

# Import AWS utils
from AWSUtils.utils import *


########################################
##### Helpers
########################################

#
# Connect to S3
#
def connect_s3(key_id, secret, session_token, region_name = None, config = None, silent = False):
    return connect_service('S3', key_id, secret, session_token, region_name, config, silent)
