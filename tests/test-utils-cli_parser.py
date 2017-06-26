# -*- coding: utf-8 -*-

import os
import shutil

from opinel.utils.cli_parser import *

class TestOpinelUtilsCliParserClass:

    def setup(self):
        if not os.path.isdir(opinel_arg_dir):
            os.makedirs(opinel_arg_dir)
        shutil.copyfile('tests/data/default_args.json', os.path.join(opinel_arg_dir, 'default.json'))

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
        parser.add_argument('foo1', help_string='I need somebody', nargs='+', default=[])
        parser.add_argument('bar1', help_string='I need somebody', action='store_true', default=False)
        parser.add_argument('foo2', help_string='I need somebody', nargs='+', default=[])
        parser.add_argument('bar2', help_string='I need somebody', action='store_true', default=False)

        # Check exception case
        try:
            parser.add_argument('opinelunittest') # Should throw an exception
            assert False
        except:
            pass

        # Invoke parse_args()
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
        tmp_opinel_arg_dir = '%s.tmp' % opinel_arg_dir
        shutil.move(opinel_arg_dir, tmp_opinel_arg_dir)
        default_args = read_default_args('awsrecipes_sort_iam_users.py')
        shutil.rmtree(opinel_arg_dir)
        assert default_args == {}
        shutil.move(tmp_opinel_arg_dir, opinel_arg_dir)
