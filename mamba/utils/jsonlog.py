import json
import re
import time

class JSONLogObserver(object):
    def __init__(self, log_file):
        self.log_file = log_file

    def __call__(self, event_dict):
        log_level = 'ERROR' if event_dict.get('isError') else 'INFO'

        log_entry = {
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(event_dict['time'])),
            'log_level': log_level,
            'system': event_dict.get('system', ''),
            'message': self.format_message(event_dict)
        }

        self.extract_message_info(log_entry)

        self.log_file.write(json.dumps(log_entry) + '\n')
        self.log_file.flush()

    def format_message(self, event_dict):
        if 'message' in event_dict:
            message = ' '.join(map(str, event_dict['message']))
            return message
        elif event_dict['isError'] and 'failure' in event_dict:
            return event_dict['failure'].getTraceback()
        else:
            return str(event_dict)

    def extract_message_info(self, log_entry):
        message = log_entry['message']
        pattern = r'(?P<ip>\d+\.\d+\.\d+\.\d+) - - \[(?P<timestamp>[^\]]+)\] "(?P<method>\w+) (?P<url>[^\s]+) [^"]+" (?P<status>\d+) (?P<size>\d+) "[^"]*" "(?P<user_agent>[^"]+)"'
        match = re.match(pattern, message)

        if match:
            log_entry.update(match.groupdict())      
