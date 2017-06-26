# -*- coding: utf-8 -*-

import copy
import shutil

from opinel.utils.cli_parser import *

class TestOpinelUtilsCliParserClass:

    def cmp(self, d1, d2, root = True):
        """
        Implement cmp() for Python3 tests

        :return
                                        -3  D1 and D2 have types that mismatch
                                        -2  D1 has more keys than D2
                                        -1  D1 has key larger than D2
                                        0   D1 and D2 are identical
                                        1   D2 has a key larger than D1
                                        2   D2 has more keys than D1
                                        3   D1 and D2 have keys with type mismatch
        """
        tmp = copy.deepcopy(d2)
        if type(d1) in [dict, list] and type(d1) != type(tmp):
            return -3 if root else 3
        elif type(d1) == dict:
            for k1 in d1:
                if k1 not in tmp:
                    return -2
                else:
                    val = tmp.pop(k1)
                    result = self.cmp(d1[k1], val, False)
                    if result != 0:
                        return result
            if len(tmp) > 0:
                return 2
        elif type(d1) == list:
            for (i, v) in enumerate(d1):
                if v != d2[i]:
                    return (v > d2[i]) - (v < d2[i])
        elif d1 != tmp:
            return (d1 > tmp) - (d1 < tmp)
        return 0

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
        parser.add_argument('bucket-name')
        parser.add_argument('group-name')
        parser.add_argument('user-name')
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
        # Test of cmp()
        tmp1 = copy.deepcopy(expected_shared_args)
        tmp1['category_groups'] = 'foobar'
        assert self.cmp(expected_shared_args, tmp1) == 3
        assert self.cmp(tmp1, 'expectedsharedargs') == -3
        tmp1 = copy.deepcopy(expected_shared_args)
        tmp1.pop('category_groups')
        assert self.cmp(tmp1, expected_shared_args) == 2
        assert self.cmp(expected_shared_args, tmp1) == -2
        tmp1 = copy.deepcopy(expected_shared_args)
        tmp1['common_groups'] = [ '0' ]
        assert self.cmp(expected_shared_args, tmp1) == 1
        assert self.cmp(tmp1, expected_shared_args) == -1
        # Test of read_default_args
        shared_args = read_default_args('shared')
        assert self.cmp(shared_args, expected_shared_args) == 0
        default_args = read_default_args('awsrecipes_foobar.py')
        assert self.cmp(default_args, expected_shared_args) == 0
        default_args = read_default_args('awsrecipes_create_iam_user.py')
        tmp1 = copy.deepcopy(expected_shared_args)
        tmp1['force_common_group'] = 'True'
        assert self.cmp(default_args, tmp1) == 0
        default_args = read_default_args('awsrecipes_sort_iam_users.py')
        tmp1 = copy.deepcopy(expected_shared_args)
        tmp1['common_groups'] = ['SomethingDifferent']
        assert self.cmp(default_args, tmp1) == 0
        tmp_opinel_arg_dir = '%s.tmp' % opinel_arg_dir
        shutil.move(opinel_arg_dir, tmp_opinel_arg_dir)
        default_args = read_default_args('awsrecipes_sort_iam_users.py')
        shutil.rmtree(opinel_arg_dir)
        assert self.cmp(default_args, {}) == 0
        shutil.move(tmp_opinel_arg_dir, opinel_arg_dir)

