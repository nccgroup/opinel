# -*- coding: utf-8 -*-
from opinel.utils.cli_parser import *

class TestOpinelUtilsCliParserClass:

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
