
# Import opinel
from opinel.utils import *


########################################
##### Helpers
########################################

#
# Connect to RDS
#
def connect_rds(key_id, secret, session_token, region_name):
    return connect_service('rds', key_id, secret, session_token, region_name)
