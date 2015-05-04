#!/usr/bin/env python2

# Import AWS utils
from AWSUtils.utils import *

# Import third-party packages
import boto
from boto import rds


########################################
##### Helpers
########################################

#
# Connect to RDS
#
def connect_rds(key_id, secret, session_token, region_name):
    try:
        return boto.rds.connect_to_region(region_name, aws_access_key_id = key_id, aws_secret_access_key = secret, security_token = session_token)
    except Exception, e:
        printException(e)
        return None
