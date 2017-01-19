
# Import opinel load_data
from opinel.load_data import *

#
# Test methods from load_data.py
#
class TestLoadDataClass:

    #
    # Unit tests for load_data()
    #
    def test_load_data(self):
        test = load_data('protocols.json', 'protocols')
        assert type(test) == dict
        assert test['1'] == 'ICMP'
        test = load_data('tests/data/protocols.json', 'protocols', True)
        assert type(test) == dict
        assert test['-2'] == 'TEST'
        # TODO : add test case without key name (both local and not local)
        test = load_data('protocols.json')
        assert type(test) == dict
        assert 'protocols' in test
        assert test['protocols']['1'] == 'ICMP'
        test = load_data('tests/data/protocols.json', local_file = True)
        assert type(test) == dict
        assert 'protocols' in test
        assert test['protocols']['-2'] == 'TEST'

