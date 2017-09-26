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
        assert (check_requirements(os.path.realpath(__file__)) == True)
        assert (check_requirements(os.path.realpath(__file__), 'tests/data/requirements1.txt') == True)
        assert (check_requirements(os.path.realpath(__file__), 'tests/data/requirements2.txt') == False)
        assert (check_requirements(os.path.realpath(__file__), 'tests/data/requirements3.txt') == False)


    def test_check_versions(self):
        assert (check_versions('1.0.0', '1.4.2', '2.0.0', 'opinelunittest') == True)
        assert (check_versions('1.0.0', '2.4.2', '2.0.0', 'opinelunittest') == True)
        assert (check_versions('1.0.0', '2.4.2', '2.0.0', 'opinelunittest', True) == False)
        assert (check_versions('1.0.0', '0.4.2', '2.0.0', 'opinelunittest') == False)
        assert (check_versions(None, None, None, None) == True)

    def test_snake_to_camel(self):
        pass

    def test_snake_to_words(self):
        pass
