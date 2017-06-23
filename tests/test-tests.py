# -*- coding: utf-8 -*-

import importlib
import os
import re
import types

from opinel.utils.console import printError

class TestTests:

    def setup(self):
        self.submodules = []
        for (root, dirnames, filenames) in os.walk('opinel'):
            for filename in filenames:
                if filename.endswith('.py') and filename != '__init__.py':
                    self.submodules.append(os.path.join(root, filename))


    def module_filename_to_parts(self, filename):
        filename = filename.replace('opinel/', '')
        part1 = os.path.dirname(filename)
        part2 = os.path.basename(filename).replace('.py', '')
        return (part1, part2)


    def test_one_testfile_per_submodule(self):
        for filename in self.submodules:
            part1, part2 = self.module_filename_to_parts(filename)
            test_filename = 'tests/test-%s-%s.py' % (part1, part2)
            try:
                assert (os.path.exists(test_filename))
                assert (os.path.isfile(test_filename))
            except:
                printError('Missing file: %s' % test_filename)
                assert (False)

    def test_call_each_testfile(self):
        with open('.travis.yml', 'rt') as f:
            contents = f.read()
        for filename in self.submodules:
            part1, part2 = self.module_filename_to_parts(filename)
            test_filename = 'tests/test-%s-%s.py' % (part1, part2)
            check = re.findall(r'%s' % test_filename, contents)
            if not check:
                printError('Missing call in Travis configuration: %s' % test_filename)
                assert (False)

    def test_one_testcase_per_function(self):
        missing_testcase = False
        for submodule_filename in self.submodules:
            submodule_name = submodule_filename.replace('/', '.').replace('.py', '')
            submodule = importlib.import_module(submodule_name)
            submodule_functions = [ f for f in dir(submodule) if type(getattr(submodule, f)) == types.FunctionType ]
            with open(submodule_filename, 'rt') as f:
                contents = f.read()
                submodule_definitions = re.findall(r'def (.*?)\(', contents)
            submodule_functions = [ f for f in submodule_functions if f in submodule_definitions ]
            part1, part2 = self.module_filename_to_parts(submodule_filename)
            testcase_filename = 'tests/test-%s-%s.py' % (part1, part2)
            with open(testcase_filename, 'rt') as f:
                contents = f.read()
                testclass_name = re.findall(r'class (.*?)(:|\()', contents)[0][0]
            testcase = importlib.import_module('tests.test-%s-%s' % (part1, part2))
            testclass = getattr(testcase, testclass_name)
            testcase_functions = [ f for f in dir(testclass) if f.startswith('test_') and callable(getattr(testclass, f)) ]
            for function in submodule_functions:
                test_function = 'test_%s' % function
                if test_function not in testcase_functions:
                    ordered_case_found = False
                    regex = re.compile('test_\d+_%s' % function)
                    for testcase_function in testcase_functions:
                        if regex.match(testcase_function):
                            ordered_case_found = True
                            break
                    if not ordered_case_found:
                        printError('Missing test case in %s: %s' % (testcase_filename, test_function))
                        missing_testcase = True
        if missing_testcase:
            assert (False)
