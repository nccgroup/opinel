#!/usr/bin/env python2

# Import AWS utils
from AWSUtils.utils import *

# Import third-party packages
import boto
from boto import ec2
from boto.ec2 import elb


########################################
##### Helpers
########################################

#
# Connect to EC2 API
#
def connect_ec2(key_id, secret, session_token,  region_name):
    return connect_service('ec2', key_id, secret, session_token, region_name)

#
# Connect to ELB API
#
def connect_elb(key_id, secret, session_token, region_name):
    try:
        return boto.ec2.elb.connect_to_region(region_name, aws_access_key_id = key_id, aws_secret_access_key = secret, security_token = session_token)
    except Exception as e:
        printException(e)
        return None
