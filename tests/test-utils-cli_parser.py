# -*- coding: utf-8 -*-

import os
import shutil

from opinel.utils.cli_parser import *

class TestOpinelUtilsCliParserClass:

    def setup(self):
        self.recipes_arg_dir = os.path.join(os.path.expanduser('~/.aws/recipes'))
        if not os.path.isdir(self.recipes_arg_dir):
            os.makedirs(self.recipes_arg_dir)
        shutil.copyfile('tests/data/default_args.json', os.path.join(self.recipes_arg_dir, 'default.json'))

    def test_class(self):
        parser = OpinelArgumentParser()
        parser.add_argument('debug')
        parser.add_argument('dry-run')
        parser.add_argument('profile')
        parser.add_argument('regions')
        parser.add_argument('partition-name')
        parser.add_argument('vpc')
        parser.add_argument('force')
        parser.add_argument('ip-ranges')
        parser.add_argument('ip-ranges-name-key')
        parser.add_argument('mfa-serial')
        parser.add_argument('mfa-code')
        parser.add_argument('csv-credentials')
        try:
            parser.add_argument('opinelunittest')
        except:
            pass

        parser.parser.add_argument('--with-coverage', dest='unittest', default=None, help='Unit test artefact')
        args = parser.parse_args()
        return

    def test_read_default_args(self):
        # 1 missed statement due to reading sys.argv[]
        expected_shared_args = {
            'category_groups': [
                'AllHumanUsers',
                'AllHeadlessUsers',
                'AllMisconfiguredUsers'
            ],
            'common_groups': [
                'AllUsers'
            ],
            'category_regex': [
                '',
                'Headless-.*',
                'MisconfiguredUser-.*'
            ]
        }
        shared_args = read_default_args('shared')
        assert shared_args == expected_shared_args
        default_args = read_default_args('awsrecipes_foobar.py')
        assert default_args == expected_shared_args
        default_args = read_default_args('awsrecipes_create_iam_user.py')
        expected_shared_args['force_common_group'] = 'True'
        assert default_args == expected_shared_args
        default_args = read_default_args('awsrecipes_sort_iam_users.py')
        expected_shared_args['common_groups'] = [ 'SomethingDifferent' ]
        expected_shared_args.pop('force_common_group')
        assert default_args == expected_shared_args
        shutil.rmtree(self.recipes_arg_dir)
        default_args = read_default_args('awsrecipes_sort_iam_users.py')
