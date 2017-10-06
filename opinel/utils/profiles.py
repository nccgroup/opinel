# -*- coding: utf-8 -*-

import os
import re

from opinel.utils.console import printDebug
from opinel.utils.credentials import read_creds

aws_dir = os.path.join(os.path.expanduser('~'), '.aws')
aws_credentials_file = os.path.join(aws_dir, 'credentials')
aws_config_file = os.path.join(aws_dir, 'config')

re_profile_name = re.compile(r'(\[(profile\s+)?(.*?)\])')

class AWSProfile(object):

    def __init__(self, filename = None, raw_profile = None, name = None, credentials = None):
        self.filename = filename
        self.raw_profile = raw_profile
        self.name = name
        if self.raw_profile:
            self.parse_raw_profile()


    def get_credentials(self):
        # For now, use the existing code...
        self.credentials = read_creds(self.name)
        return self.credentials


    def parse_raw_profile(self):
        for line in self.raw_profile.split('\n')[1:]:
            line = line.strip()
            if line:
                values = line.split('=')
                attribute = values[0].strip()
                value = ''.join(values[1:]).strip()
                setattr(self, attribute, value)



class AWSProfiles(object):

    @staticmethod
    def list(filters = []):
        """
        @brief

        :return:                        List of all profile names found in .aws/config and .aws/credentials
        """
        return [p.name for p in AWSProfiles.get(filters)]


    @staticmethod
    def get(names = []):
        """
        """
        profiles = []
        profiles += AWSProfiles.find_profiles_in_file(aws_credentials_file, names)
        profiles += AWSProfiles.find_profiles_in_file(aws_config_file, names)
        return profiles


    @staticmethod
    def find_profiles_in_file(filename, names = []):
        profiles = []
        if type(names) != list:
            names = [ names ]
        printDebug('Searching for profiles matching %s in %s ... ' % (str(names), filename))
        name_filters = []
        for name in names:
            name_filters.append(re.compile('^%s$' % name))
        with open(filename, 'rt') as f:
            aws_credentials = f.read()
            existing_profiles = re_profile_name.findall(aws_credentials)
            profile_count = len(existing_profiles) - 1
            for i, profile in enumerate(existing_profiles):
                matching_profile = False
                raw_profile = None
                for name_filter in name_filters:
                    if name_filter.match(profile[2]):
                        matching_profile = True
                        i1 = aws_credentials.index(profile[0])
                        if i < profile_count:
                            i2 = aws_credentials.index(existing_profiles[i+1][0])
                            raw_profile = aws_credentials[i1:i2]
                        else:
                            raw_profile = aws_credentials[i1:]
                if len(name_filters) == 0 or matching_profile:
                    profiles.append(AWSProfile(filename = filename, raw_profile = raw_profile, name = profile[2]))
        return profiles

