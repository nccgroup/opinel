#!/usr/bin/env python2

# Import third-party packages
import argparse
import sys
import traceback


########################################
##### Debug-related functions
########################################

def printException(e):
    global verbose_exceptions
    if verbose_exceptions:
        print traceback.format_exc()
    else:
        print e

def configPrintException(enable):
    global verbose_exceptions
    verbose_exceptions = enable


########################################
##### Prompt functions
########################################

def prompt_4_value(question):
    sys.stdout.write(question)
    return raw_input()

def prompt_4_yes_no(question):
    while True:
        sys.stdout.write(question + ' (y/n)? ')
        choice = raw_input().lower()
        if choice == 'yes' or choice == 'y':
            return True
        elif choice == 'no' or choice == 'n':
            return False
        else:
            print '\'%s\' is not a valid answer. Enter \'yes\'(y) or \'no\'(n).' % choice

########################################
##### Argument parser
########################################

parser = argparse.ArgumentParser()

parser.add_argument('--debug',
                    dest='debug',
                    default=False,
                    action='store_true',
                    help='Print the stack trace when exception occurs')
