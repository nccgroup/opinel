
# Import opinel
from opinel.utils import *


########################################
##### Helpers
########################################

#
# Connect to S3
#
def connect_s3(key_id, secret, session_token, region_name = None, config = None, silent = False):
    return connect_service('S3', key_id, secret, session_token, region_name, config, silent)

#
# Get bucket location
#
def get_s3_bucket_location(s3_client, bucket_name):
    location = s3_client.get_bucket_location(Bucket = bucket_name)
    return location['LocationConstraint'] if location['LocationConstraint'] else 'us-east-1'
