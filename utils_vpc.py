#!/usr/bin/env python2

# Import AWS utils
from AWSUtils.utils import *

# Import third-party packages
import boto
from boto import vpc


########################################
##### Helpers
########################################

#
# Connect to VPC API
#
def connect_vpc(key_id, secret, session_token, region_name):
    try:
        return boto.vpc.connect_to_region(region_name, aws_access_key_id = key_id, aws_secret_access_key = secret, security_token = session_token)
    except Exception as e:
        printException(e)
        return None
