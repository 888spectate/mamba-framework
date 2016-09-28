# -*- test-case-name: mamba.test.test_logger -*-
# Copyright (c) 2012 Oscar Campos <oscar.campos@member.fsf.org>
# See LICENSE for more details

"""
Mamba logger utilities
"""
import time
import syslog as std_syslog

from twisted.python import syslog
from storm.tracer import debug as storm_debug


class StormDebugLogFile(object):
    """Log storm traces to the log directory
    """
    def __init__(self):
        self._observer = syslog.SyslogObserver(
            'storm_debug', syslog.DEFAULT_OPTIONS, std_syslog.LOG_DEBUG
        )

    def write(self, msg):
        self._observer.emit({
            'message': [str(msg)],
            'time': time.time(),
            'isError': 0,
            'system': 'storm_debug'
        })

    def flush(self):
        pass

    @classmethod
    def start(cls):
        """Start logging
        """
        storm_debug(True, stream=cls())

    @staticmethod
    def stop():
        """Stop logging
        """
        storm_debug(False)
