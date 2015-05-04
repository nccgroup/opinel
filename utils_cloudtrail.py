#!/usr/bin/env python2

# Import AWS utils
from AWSUtils.utils import *

# Import third-party packages
import boto
from boto import cloudtrail


########################################
##### Helpers
########################################

#
# Connect to Cloudtrail
#
def connect_cloudtrail(profile_name, region_name):
    try:
        session_key_id, session_secret, mfa_serial, session_token = read_creds_from_aws_credentials_file(profile_name)
        return cloudtrail.connect_to_region(region_name, aws_access_key_id = session_key_id, aws_secret_access_key = session_secret, security_token = session_token)
    except Exception, e:
        printException(e)
        return None
