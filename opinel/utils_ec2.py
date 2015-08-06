
# Import opinel
from opinel.utils import *


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
    return connect_service('elb', key_id, secret, session_token, region_name)
