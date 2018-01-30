import syslog
from twisted.python.log import msg as twisted_msg
from twisted.python.log import err as twisted_error


def _prepend_msg_severity(severity, args):
    args_list = list(args)
    args_list[0] = "[%s] %s" % (severity, args_list[0])
    return args_list


def _prepend_err_severity(severity, args):
    args_list = list(args)
    if len(args_list) == 2:
        args_list[1] = "[%s] %s" % (severity, args_list[1])
    elif len(args_list) == 0:
        args_list = [None, "[%s] %s" % (severity, "Unhandled exception")]
    elif isinstance(args_list[0], (str, unicode)):
        args_list[0] = "[%s] %s" % (severity, args_list[0])

    return args_list


def debug(*args, **kwargs):
    kwargs['syslogPriority'] = syslog.LOG_DEBUG
    twisted_msg(*_prepend_msg_severity("DEBUG", args), **kwargs)


def msg(*args, **kwargs):
    debug(*args, **kwargs)


def info(*args, **kwargs):
    kwargs['syslogPriority'] = syslog.LOG_INFO
    twisted_msg(*_prepend_msg_severity("INFO", args), **kwargs)


def warning(*args, **kwargs):
    kwargs['syslogPriority'] = syslog.LOG_WARNING
    twisted_msg(*_prepend_msg_severity("WARNING", args), **kwargs)


def error(*args, **kwargs):
    kwargs['syslogPriority'] = syslog.LOG_ERR
    twisted_error(*_prepend_err_severity("ERROR", args), **kwargs)


def err(*args, **kwargs):
    error(*args, **kwargs)


def critical(*args, **kwargs):
    kwargs['syslogPriority'] = syslog.LOG_CRIT
    twisted_error(*_prepend_err_severity("CRITICAL", args), **kwargs)
