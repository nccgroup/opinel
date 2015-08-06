
# Import opinel
from opinel.utils import *


########################################
##### Helpers
########################################

#
# Connect to Cloudtrail
#
def connect_cloudtrail(key_id, secret, session_token, region, silent = False):
    return connect_service('CloudTrail', key_id, secret, session_token, region_name = region, silent = silent)

#
# Get the list of trails for a given region
#
def get_trails(cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    return trails['trailList']
