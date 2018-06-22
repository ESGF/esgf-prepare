#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Useful functions to use with this package.

"""

import os
import sys
from ctypes import c_char_p
from multiprocessing import Value
from constants import SHELL_COLORS
from custom_exceptions import *


class COLOR:
    """
    Define color object for print statements
    Default is no color (i.e., restore original color)

    """
    PALETTE = {color: i + 30 for (color, i) in SHELL_COLORS.items()}
    PALETTE.update({'light ' + color: i + 90 for (color, i) in SHELL_COLORS.items()})
    RESTORE = '\033[{}m'

    def __init__(self, color=None):
        if color in COLOR.PALETTE.keys():
            color = COLOR.PALETTE[color]
        else:
            color = 0
        assert isinstance(color, int)
        self.color = '\033[{}m'.format(str(n))

    def bold(self, msg=None):
        self.color.replace('[', '[1;')
        return self.__call__(msg)

    def italic(self, msg=None):
        self.color.replace('[', '[3;')
        return self.__call__(msg)

    def underline(self, msg=None):
        self.color.replace('[', '[4;')
        return self.__call__(msg)

    def blink(self, msg=None):
        self.color.replace('[', '[5;')
        return self.__call__(msg)

    def __call__(self, msg):
        if msg:
            return self.color + msg + COLOR.RESTORE
        else:
            return self.color


class COLORS:
    """
    String colors for print statements

    """
    def __init__(self):
        pass

    @staticmethod
    def OKBLUE(msg):
        return COLOR('blue')(msg)

    @staticmethod
    def HEADER(msg):
        return COLOR('magenta').bold(msg)

    @staticmethod
    def SUCCESS(msg):
        return COLOR('green').bold(msg)

    @staticmethod
    def FAIL(msg):
        return COLOR('red').bold(msg)

    @staticmethod
    def INFO(msg):
        return COLOR('cyan')(msg)

    @staticmethod
    def WARNING(msg):
        return COLOR('light red').bold(msg)

    @staticmethod
    def ERROR(msg):
        return COLOR('red').bold(msg)

    @staticmethod
    def DEBUG(msg):
        return COLOR('cyan').bold(msg)


class TAGS:
    """
    Tags strings for print statements

    """
    SKIP = COLORS.WARNING(':: SKIPPED :: ')
    FETCH = COLORS.SUCCESS(':: FETCHED :: ')
    DEBUG = COLORS.DEBUG(':: DEBUG   :: ')
    INFO = COLORS.INFO(':: INFO    :: ')
    WARNING = COLORS.WARNING(':: WARNING :: ')
    ERROR = COLORS.ERROR(':: ERROR   :: ')
    SUCCESS = COLORS.SUCCESS(':: SUCCESS :: ')
    FAIL = COLORS.FAIL(':: FAIL    :: ')
    LOG = COLORS.HEADER(':: LOG     :: ')
    COMMAND = COLORS.HEADER(':: COMMAND :: ')

    def __init__(self):
        pass


class Print(object):
    """
    Class to manage and dispatch print statement depending on log and debug mode.

    """
    LOG = None
    DEBUG = False
    CMD = None
    BUFFER = Value(c_char_p, '')
    LOGFILE = None
    ERRFILE = None
    CARRIAGE_RETURNED = True

    @staticmethod
    def init(log, debug, cmd):
        Print.LOG = log
        Print.DEBUG = debug
        Print.CMD = cmd
        logname = '{}-{}'.format(Print.CMD, datetime.now().strftime("%Y%m%d-%H%M%S"))
        if Print.LOG:
            logdir = Print.LOG
            if not os.path.isdir(Print.LOG):
                os.makedirs(Print.LOG)
        else:
            logdir = os.getcwd()
        Print.LOGFILE = os.path.join(logdir, logname + '.log')
        Print.ERRFILE = os.path.join(logdir, logname + '.err')

    @staticmethod
    def check_carriage_return(msg):
        if msg.endswith('\n') or '\r' in msg:
            Print.CARRIAGE_RETURNED = True
        else:
            Print.CARRIAGE_RETURNED = False

    @staticmethod
    def print_to_stdout(msg):
        Print.check_carriage_return(msg)
        sys.stdout.write(msg)
        sys.stdout.flush()

    @staticmethod
    def print_to_logfile(msg):
        Print.check_carriage_return(msg)
        with open(Print.LOGFILE, 'a+') as f:
            for color in COLORS.__dict__.values():
                msg = msg.replace(color, '')
            f.write(msg)

    @staticmethod
    def progress(msg):
        if not Print.CARRIAGE_RETURNED:
            msg = '\n' + msg
        if Print.LOG:
            Print.print_to_stdout(msg)
        elif not Print.DEBUG:
            Print.print_to_stdout(msg)

    @staticmethod
    def command(msg):
        msg = TAGS.COMMAND + COLOR('magenta')(msg) + '\n'
        if not Print.CARRIAGE_RETURNED:
            msg = '\n' + msg
        if Print.LOG:
            Print.print_to_logfile(msg)
        elif Print.DEBUG:
            Print.print_to_stdout(msg)

    @staticmethod
    def log(msg=None):
        if msg:
            msg = TAGS.LOG + COLOR('magenta')(msg) + '\n'
        else:
            msg = TAGS.LOG + Print.LOGFILE + '\n'
        if not Print.CARRIAGE_RETURNED:
            msg = '\n' + msg
        if Print.LOG:
            Print.print_to_stdout(msg)

    @staticmethod
    def summary(msg):
        msg += '\n'
        if not Print.CARRIAGE_RETURNED:
            msg = '\n' + msg
        if Print.LOG:
            Print.print_to_stdout(msg)
            Print.print_to_logfile(msg)
        else:
            Print.print_to_stdout(msg)

    @staticmethod
    def info(msg):
        msg += '\n'
        if not Print.CARRIAGE_RETURNED:
            msg = '\n' + msg
        if Print.LOG:
            Print.print_to_logfile(msg)
        elif Print.DEBUG:
            Print.print_to_stdout(msg)

    @staticmethod
    def debug(msg):
        msg = TAGS.DEBUG + msg + '\n'
        if not Print.CARRIAGE_RETURNED:
            msg = '\n' + msg
        if Print.DEBUG:
            if Print.LOG:
                Print.print_to_logfile(msg)
            else:
                Print.print_to_stdout(msg)

    @staticmethod
    def warning(msg):
        msg = TAGS.WARNING + COLOR().bold(msg) + '\n'
        if not Print.CARRIAGE_RETURNED:
            msg = '\n' + msg
        if Print.LOG:
            Print.print_to_logfile(msg)
        else:
            Print.print_to_stdout(msg)

    @staticmethod
    def error(msg, buffer=False):
        msg = TAGS.ERROR + msg + '\n'
        if not Print.CARRIAGE_RETURNED:
            msg = '\n' + msg
        if Print.LOG:
            Print.print_to_logfile(msg)
        elif buffer:
            Print.BUFFER.value += msg
        elif Print.DEBUG:
            Print.print_to_stdout(msg)
        else:
            Print.print_to_stdout(msg)

    @staticmethod
    def success(msg, buffer=False):
        msg = TAGS.SUCCESS + msg + '\n'
        if not Print.CARRIAGE_RETURNED:
            msg = '\n' + msg
        if Print.LOG:
            Print.print_to_logfile(msg)
        elif buffer:
            Print.BUFFER.value += msg
        elif Print.DEBUG:
            Print.print_to_stdout(msg)
        else:
            Print.print_to_stdout(msg)

    @staticmethod
    def exception(msg, buffer=False):
        msg += '\n'
        if not Print.CARRIAGE_RETURNED:
            msg = '\n' + msg
        if Print.LOG:
            Print.print_to_logfile(msg)
        elif Print.DEBUG:
            Print.print_to_stdout(msg)
        elif buffer:
            Print.BUFFER.value += msg
        else:
            Print.print_to_stdout(msg)

    @staticmethod
    def flush():
        if Print.BUFFER.value:
            if Print.LOG:
                Print.print_to_logfile(Print.BUFFER.value)
            else:
                Print.print_to_stdout(Print.BUFFER.value)
            Print.BUFFER.value = ''
