
# Import opinel
from opinel.utils import *


########################################
##### Helpers
########################################

#
# Connect to Redshift
#
def connect_redshift(credentials, region):
    return connect_service('redshift', credentials, region)
