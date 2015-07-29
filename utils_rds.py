#!/usr/bin/env python2

# Import AWS utils
from AWSUtils.utils import *


########################################
##### Helpers
########################################

#
# Connect to RDS
#
def connect_rds(key_id, secret, session_token, region_name):
    return connect_service('rds', key_id, secret, session_token, region_name)
