# -*- coding: utf-8 -*-

from opinel.utils.console import *

class TestOpinelUtilsConsoleClass:

    def test_configPrintException(self):
        configPrintException(False)
        configPrintException(True)


    def test_printDebug(self):
        printDebug('hello')


    def test_printError(self):
        printError('hello', False)
        printError('hello')


    def test_printException(self):
        configPrintException(True)
        try:
            raise Exception('opinelunittest')
        except Exception as e:
            printException(e)
        configPrintException(False)
        try:
            raise Exception('opinelunittest')
        except Exception as e:
            printException(e)
        try:
            raise Exception('opinelunittest')
        except:
            printException(e, True)


    def test_printInfo(msg, newLine=True):
        printInfo('hello', False)
        printInfo('hello')


    def test_printGeneric(self):
        printGeneric(sys.stdout, 'hello', False)
        printGeneric(sys.stderr, 'hello')


    def test_prompt(self):
        assert prompt('a') == 'a'
        assert prompt('') == ''
        test = ['a', 'b']
        assert prompt(test) == 'a'
        assert prompt(test) == 'b'
        assert prompt(test) == ''


    def test_prompt_4_mfa_code(self):
        prompt_4_mfa_code(input='q')
        prompt_4_mfa_code(input='012345')
        prompt_4_mfa_code(input='0123456789')
        prompt_4_mfa_code(input=['helloworld', '0123456'])
        prompt_4_mfa_code(activate=True, input='012345')
        prompt_4_mfa_code(activate=True, input='q')


    def test_prompt_4_mfa_serial(self):
        prompt_4_mfa_serial(['a', 'n', 'arn:aws:iam::123456789012:mfa/username', 'y'])


    def test_prompt_4_overwrite(self):
        assert prompt_4_overwrite(os.path.realpath(__file__), True) == True
        assert prompt_4_overwrite(os.path.realpath(__file__), False, input='y') == True
        assert prompt_4_overwrite(os.path.realpath(__file__), False, input='n') == False


    def test_prompt_4_value(self):
        assert prompt_4_value('prompt_4_value', no_confirm=True, input='inputvalue') == 'inputvalue'
        assert prompt_4_value('prompt_4_value', no_confirm=True, is_question=True, input='inputvalue') == 'inputvalue'
        assert prompt_4_value('prompt_4_value', choices=['a', 'b', 'c'], no_confirm=True, input='b') == 'b'
        assert prompt_4_value('prompt_4_value', choices=['a', 'b', 'c'], display_choices=False, no_confirm=True, input='b') == 'b'
        assert prompt_4_value('prompt_4_value', choices=['a', 'b', 'c'], display_indices=True, no_confirm=True, input='1') == 'b'
        assert prompt_4_value('prompt_4_value', choices=['a', 'b', 'c'], default='b', no_confirm=True, input='') == 'b'
        assert prompt_4_value('prompt_4_value', choices=['a', 'b', 'c'], no_confirm=True, authorize_list=True, input='a,b') == 'a,b'
        assert prompt_4_value('prompt_4_value', choices=['a', 'b', 'c'], required=True, no_confirm=True, input=['', 'b']) == 'b'
        assert prompt_4_value('prompt_4_value', choices=['a', 'b', 'c'], required=True, no_confirm=True, input=['invalid', 'b']) == 'b'
        assert prompt_4_value('prompt_4_value', choices=['a', 'b', 'c'], no_confirm=True, input='a,c') == None
        assert prompt_4_value('prompt_4_value', choices=['a', 'b', 'c'], no_confirm=True, input='a,b', authorize_list = True) == 'a,b'
        assert prompt_4_value('prompt_4_value', choices=['a', 'b', 'c'], no_confirm=True, input='a,e', authorize_list = True) == None
        assert prompt_4_value('prompt_4_value', regex=re_mfa_serial_format, regex_format=mfa_serial_format, required=True, input=['inputvalue', 'arn:aws:iam::123456789012:mfa/username', 'y']) == 'arn:aws:iam::123456789012:mfa/username'
        assert prompt_4_value('prompt_4_value', regex=re_mfa_serial_format, regex_format=mfa_serial_format, required=False, input=['inputvalue', '', 'y']) == ''




    def test_prompt_4_yes_no(self):
        assert prompt_4_yes_no('hello', input='N') == False
        assert prompt_4_yes_no('hello', input='no') == False
        assert prompt_4_yes_no('hello', input='Y') == True
        assert prompt_4_yes_no('hello', input='yes') == True
        assert prompt_4_yes_no('hello', input=['foo', 'bar', 'no']) == False
        assert prompt_4_yes_no('hello', input='Ye') == None
        assert prompt_4_yes_no('hello', input='Non') == None
        return
