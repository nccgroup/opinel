#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse



class OpinelArgumentParser(object):
    """
    """

    def __init__(self):
        self.parser = argparse.ArgumentParser()


    def add_argument(self, argument_name, default_args = None):
        if argument_name == 'debug':
            self.parser.add_argument('--debug',
                                dest='debug',
                                default=False,
                                action='store_true',
                                help='Print the stack trace when exception occurs')
        elif argument_name == 'dry-run':
            self.parser.add_argument('--dry-run',
                                dest='dry_run',
                                default=False,
                                action='store_true',
                                help='Executes read-only actions (check status, describe*, get*, list*...)')
        elif argument_name == 'profile':
            self.parser.add_argument('--profile',
                                dest='profile',
                                default= ['default'],
                                nargs='+',
                                help='Name of the profile')
        elif argument_name == 'regions':
            self.parser.add_argument('--regions',
                                dest='regions',
                                default=[],
                                nargs='+',
                                help='Name of regions to run the tool in, defaults to all')
        elif argument_name == 'partition-name':
            self.parser.add_argument('--partition-name',
                                dest='partition_name',
                                default='aws',
                                help='Switch out of the public AWS partition (e.g. US gov or China)')
        elif argument_name == 'vpc':
            self.parser.add_argument('--vpc',
                                dest='vpc',
                                default=[],
                                nargs='+',
                                help='Name of VPC to run the tool in, defaults to all')
        elif argument_name == 'force':
            self.parser.add_argument('--force',
                                dest='force_write',
                                default=False,
                                action='store_true',
                                help='Overwrite existing files')
        elif argument_name == 'ip-ranges':
            self.parser.add_argument('--ip-ranges',
                                dest='ip_ranges',
                                default=[],
                                nargs='+',
                                help='Config file(s) that contain your known IP ranges.')
        elif argument_name == 'ip-ranges-key-name':
            self.parser.add_argument('--ip-ranges-key-name',
                                dest='ip_ranges_key_name',
                                default='name',
                                help='Name of the key containing the display name of a known CIDR.')
        elif argument_name == 'mfa-serial':
            self.parser.add_argument('--mfa-serial',
                                dest='mfa_serial',
                                default=None,
                                help='')
        elif argument_name == 'mfa-code':
            self.parser.add_argument('--mfa-code',
                                dest='mfa_code',
                                default=None,
                                help='')
        elif argument_name == 'csv-credentials':
            self.parser.add_argument('--csv-credentials',
                                dest='csv_credentials',
                                default=None,
                                help='')
        else:
            raise Exception('Invalid parameter name %s' % argument_name)
