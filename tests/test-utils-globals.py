# -*- coding: utf-8 -*-

from opinel.utils.globals import *

class TestOpinelUtils:

    def callback(self, object):
        object['foo'] = 'bar'


    def test_manage_dictionary(self):
        test = {}
        manage_dictionary(test, 'a', [])
        assert 'a' in test
        assert type(test['a']) == list
        manage_dictionary(test, 'a', {})
        assert test['a'] == []
        manage_dictionary(test, 'b', {}, self.callback)
        assert type(test['b'] == dict)
        assert ('foo' in test['b'])
        assert test['b']['foo'] == 'bar'


    def test_check_requirements(self): # script_path):
        check_requirements(os.path.realpath(__file__))


    def test_check_versions(self):
        check_versions('1.0.0', '1.4.2', '2.0.0', 'opinelunittest')
        check_versions('1.0.0', '2.4.2', '2.0.0', 'opinelunittest')
        check_versions('1.0.0', '0.4.2', '2.0.0', 'opinelunittest')
        check_versions(None, None, None, None)
