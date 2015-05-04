#!/usr/bin/env python2

# Import AWS utils
from AWSUtils.utils import *

# Import third-party packages
import boto


########################################
##### Helpers
########################################

#
# Connect to S3
#
def connect_s3(key_id, secret, session_token):
    try:
        return boto.connect_s3(aws_access_key_id = key_id, aws_secret_access_key = secret, security_token = session_token)
    except Exception, e:
        printException(e)
        return None
