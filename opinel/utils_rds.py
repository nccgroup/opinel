
# Import opinel
from opinel.utils import *


########################################
##### Helpers
########################################

#
# Connect to RDS
#
def connect_rds(credentials, region_name):
    return connect_service('rds', credentials, region_name)
