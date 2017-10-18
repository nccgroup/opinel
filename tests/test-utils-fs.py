# -*- coding: utf-8 -*-

import datetime

from opinel.utils.fs import *
from opinel.utils.console import configPrintException, printError

class TestOpinelFsClass:
    """
    Test opinel.fs
    """

    def cmp(self, a, b):
        """
        Implement cmp() for Python3 tests
        """
        return (a > b) - (a < b)

    def setup(self):
        configPrintException(True)

    def test_CustomJSONEncoder(self):
        date = datetime.datetime(2017, 6, 12)
        blob1 = {'foo': 'bar', 'date': date}
        print('%s' % json.dumps(blob1, cls=CustomJSONEncoder))
        blob2 = {'foo': 'bar', 'baz': {'foo': 'bar'}}
        print('%s' % json.dumps(blob2, cls=CustomJSONEncoder))

    def test_load_data(self):
        test = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data/protocols.json')
        load_data(test, local_file=True)
        load_data(test, 'protocols', local_file=True)
        load_data('protocols.json', 'protocols')
        load_data('ip-ranges/aws.json', 'prefixes')
        load_data('tests/data/protocols.json', 'protocols', local_file=True)
        test = load_data('protocols.json', 'protocols')
        assert type(test) == dict
        assert test['1'] == 'ICMP'
        test = load_data('tests/data/protocols.json', 'protocols', True)
        assert type(test) == dict
        assert test['-2'] == 'TEST'
        test = load_data('tests/data/protocols.yaml', 'protocols', True, format = 'yaml')
        assert type(test) == dict
        assert test['-2'] == 'TEST'
        test = load_data('tests/data/protocols.txt', local_file = True, format = 'txt')
        assert (test.rstrip() == 'some text here')
        test = load_data('tests/data/protocols.json', 'protocols', True, format = 'unknown')
        assert test == None


    def test_read_default_args(self):
        pass


    def test_read_ip_ranges(self):
        read_ip_ranges('ip-ranges/aws.json', local_file=False)
        read_ip_ranges('tests/data/ip-ranges-1.json', local_file=True)
        read_ip_ranges('tests/data/ip-ranges-1.json', local_file=True, ip_only=True)
        successful_read_ip_ranges_runs = True
        test_cases = [
            {
                'filename': 'tests/data/ip-ranges-1.json',
                'local_file': True,
                'conditions': [],'ip_only': False,
                'results': 'tests/results/read_ip_ranges/ip-ranges-1a.json'
            },
            {
                'filename': 'tests/data/ip-ranges-1.json',
                'local_file': True,
                'conditions': [],'ip_only': True,
                'results': 'tests/results/read_ip_ranges/ip-ranges-1b.json'
            },
            {
                'filename': 'tests/data/ip-ranges-1.json',
                'local_file': True,
                'conditions': [
                         [
                          'field_a', 'equal', 'a1']],
                'ip_only': True,
                'results': 'tests/results/read_ip_ranges/ip-ranges-1c.json'
            },
            {
                'filename': 'ip-ranges/aws.json',
                'local_file': False,
                'conditions': [
                    [ 'ip_prefix', 'equal', '23.20.0.0/14' ]
                ],
                'ip_only': False,
                'results': 'tests/results/read_ip_ranges/ip-ranges-a.json'
            },
            {
                "filename": 'tests/data/ip-ranges-3.json',
                "local_file": True,
                'results': None,
                "ip_only": True,
                "results": "tests/results/read_ip_ranges/ip-ranges-3.json"
            },
            {
                "filename": 'tests/data/ip-ranges-3.json',
                "local_file": True,
                'results': None,
                "ip_only": True,
                "results": "tests/results/read_ip_ranges/ip-ranges-3.json"
            }
        ]
        for test_case in test_cases:
            results = test_case.pop('results')
            test_results = read_ip_ranges(**test_case)
            known_results = load_data(results, local_file=True)
            if self.cmp(test_results, known_results) != 0:
                successful_read_ip_ranges_runs = False

        assert successful_read_ip_ranges_runs

    def test_save_blob_as_json(self):
        date = datetime.datetime.now()
        save_blob_as_json('tmp1.json', {'foo': 'bar','date': date}, True, False)
        save_blob_as_json('tmp1.json', {'foo': 'bar'}, True, True)
        save_blob_as_json('/root/tmp1.json', {'foo': 'bar'}, True, True)

    def test_save_ip_ranges(self):
        if os.path.isfile('ip-ranges-default.json'):
            os.remove('ip-ranges-default.json')
        save_ip_ranges('default', ['1.2.3.4'], False, False)
        save_ip_ranges('default', [{'ip_prefix': '5.6.7.8'}], True, True)

    def test_read_file(self):
        test = read_file('tests/data/protocols.txt')
        assert (test.rstrip() == 'some text here')
