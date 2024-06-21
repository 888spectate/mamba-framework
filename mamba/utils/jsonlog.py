import json
import re
import time

class JSONLogObserver(object):
    def __init__(self, log_file):
        self.log_file = log_file
        self.buffered_log_entry = None

    def __call__(self, event_dict):
        log_level = 'ERROR' if event_dict.get('isError') else 'INFO'

        log_entry = {
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(event_dict['time'])),
            'log_level': log_level,
            'system': event_dict.get('system', ''),
            'message': self.format_message(event_dict)
        }
        
        # Handle multi-line messages
        if self.buffered_log_entry and log_entry['log_level'] == self.buffered_log_entry['log_level'] and log_entry["message"].startswith(' '):
            self.buffered_log_entry['message'] += '\n' + log_entry['message']
        else:
            if self.buffered_log_entry:
                self.extract_message_info(log_entry)
                self.log_file.write(json.dumps(self.buffered_log_entry) + '\n')
                self.log_file.flush()
            self.buffered_log_entry = log_entry

    def format_message(self, event_dict):
        if 'message' in event_dict:
            message = '\n'.join(map(str, event_dict['message']))
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
