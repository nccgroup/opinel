

########################################
##### Helpers
########################################

#
# Get the list of trails for a given region
#
def get_trails(cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    return trails['trailList']
