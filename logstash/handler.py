import json
import traceback
import socket
from logging.handlers import DatagramHandler
from datetime import datetime


class LogstashHandler(DatagramHandler):
    """Python logging handler for Logstash
    :param host: The host of the logstash server.
    :param port: The port of the logstash server (default 5959).
    :param message_type: The type of the message (default logstash).
    :param fqdn; Indicates whether to show fully qualified domain name or not (default False).
    """

    def __init__(self, host, port=5959, message_type='logstash', fqdn=False):
        self.message_type = message_type
        self.fqdn = fqdn
        DatagramHandler.__init__(self, host, port)

    def makePickle(self, record):
        message_dict = self.build_message(record)
        return json.dumps(message_dict)

    def build_message(self, record):
        add_debug_info = False

        if self.fqdn:
            host = socket.getfqdn()
        else:
            host = socket.gethostname()

        message_dict = {
            '@fields': {
                'levelname': record.levelname,
                'logger': record.name,
            },
            '@message': record.getMessage(),
            '@source': host,
            '@tags': [],
            '@timestamp': self.format_timestamp(record.created),
            '@type': self.message_type,
        }

        if record.exc_info:
            add_debug_info = True
            self.add_message_field(message_dict, 'exc_info', self.format_exception(record.exc_info))

        if add_debug_info:
            self.add_message_field(message_dict, 'pathname', record.pathname)
            self.add_message_field(message_dict, 'lineno', record.lineno)
            self.add_message_field(message_dict, 'process', record.process)
            self.add_message_field(message_dict, 'threadName', record.threadName)
            self.add_message_field(message_dict, 'lineno', record.lineno)
            # funName was added in 2.5
            if not getattr(record, 'funcName', None):
                self.add_message_field(message_dict, 'funcName', record.funcName)
            # processName was added in 2.6
            if not getattr(record, 'processName', None):
                self.add_message_field(message_dict, 'processName', record.processName)

        message_dict = self.add_extra_fields(message_dict, record)

        return message_dict

    def add_message_field(self, message_dict, key, value):
        message_dict['@fields'][key] = repr(value)

    def add_extra_fields(self, message_dict, record):
        # The list contains all the attributes listed in
        # http://docs.python.org/library/logging.html#logrecord-attributes
        skip_list = (
            'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
            'funcName', 'id', 'levelname', 'levelno', 'lineno', 'module',
            'msecs', 'msecs', 'message', 'msg', 'name', 'pathname', 'process',
            'processName', 'relativeCreated', 'thread', 'threadName')

        for key, value in record.__dict__.items():
            if key not in skip_list:
                self.add_message_field(message_dict, key, value)

        return message_dict

    def format_exception(self, exc_info):
        return '\n'.join(traceback.format_exception(*exc_info)) if exc_info else ''

    def format_timestamp(self, time):
        return datetime.utcfromtimestamp(time).isoformat()