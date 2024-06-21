import json
import time
from twisted.python import log

class JSONLogObserver(object):
    def __init__(self, log_file):
        self.log_file = log_file
        
    def emit(self, event_dict):
        log_level = 'ERROR' if event_dict.get('isError') else 'INFO'
        
        log_entry = {
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(event_dict['time'])),
            'log_level': log_level,
            'system': event_dict.get('system', ''),
            'message': self.format_message(event_dict)
        }
        
        self.log_file.write(json.dumps(log_entry) + '\n')
        self.log_file.flush()
        
    def format_message(self, event_dict):
        if 'message' in event_dict:
            return ' '.join(map(str, event_dict['message']))
        elif event_dict['isError'] and 'failure' in event_dict:
            return event_dict['failure'].getTraceback()
        else:
            return str(event_dict)