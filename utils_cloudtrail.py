#!/usr/bin/env python2

# Import AWS utils
from AWSUtils.utils import *

# Import third-party packages
import boto
from boto import cloudtrail
from collections import Counter


########################################
##### Helpers
########################################

#
# Connect to Cloudtrail
#
def connect_cloudtrail(key_id, secret, session_token, region_name):
    try:
        return cloudtrail.connect_to_region(region_name, aws_access_key_id = key_id, aws_secret_access_key = secret, security_token = session_token)
    except Exception, e:
        printException(e)
        return None

#
# Get the list of trails for a given region
#
def get_trails(cloudtrail_connection):
    trails = cloudtrail_connection.describe_trails()
    return trails['trailList']
