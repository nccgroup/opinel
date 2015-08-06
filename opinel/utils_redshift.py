
# Import opinel
from opinel.utils import *


########################################
##### Helpers
########################################

#
# Connect to Redshift
#
def connect_redshift(key_id, secret, session_token, region):
    return connect_service('redshift', key_id, secret, session_token, region)
