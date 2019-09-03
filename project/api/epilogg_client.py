import requests
import datetime
import time
import json
import uuid

FormatPlain = 0
FormatJson = 1
FormatXML = 2
FormatYAML = 3

LevelNotSet = 0
LevelDebug = 10
LevelInfo = 20
LevelWarning = 30
LevelError = 40
LevelCritical = 50

DirectionNone = 0
DirectionRequest = 1
DirectionResponse = 2

EPILOGG_USER_AGENT = "epi:logg API Client"


#**************************************************************************************************


class APIClient(object):
    api_url = None
    token = None
    client_id = None
    format = FormatPlain
    buffered = False
    log_buffer = None

    #----------------------------------------------------------------------------------------------

    def __init__(self, api_url, token, client_id, format=FormatPlain, buffered=False):
        self.api_url = api_url
        self.token = token
        self.client_id = client_id
        self.format = format
        self.buffered = buffered
        self.log_buffer = [] if buffered else None

    #----------------------------------------------------------------------------------------------

    def create_group_id(self):
        return str(int(time.time() * 10**10))

    #----------------------------------------------------------------------------------------------

    def send_data(self, command, data):
        data.update({
            'command': command,
            'client_id': self.client_id,
        })

        headers = {
            'Authorization': 'Token {}'.format(self.token),
            'User-Agent': EPILOGG_USER_AGENT,
        }

        try:
            response = requests.post(
                url=self.api_url,
                json=data,
                headers=headers,
            )
            return response.status_code == 200
        except:
            return False

    #----------------------------------------------------------------------------------------------

    def log(self, level, data, category=None, direction=None, format=None, vars=None, group=None):
        variables = []
        if vars is not None:
            for v in vars:
                variables.append({
                    'name': v,
                    'type': str(type(vars[v])),
                    'value': str(vars[v]),
                })

        data = {
            'data': data,
            'format': format if format is not None else self.format,
            'level': level,
            'category': category,
            'group': group,
            'variables': json.dumps(variables) if len(variables) else None,
            'direction': direction,
            'timestamp': str(datetime.datetime.now()),
        }

        if self.buffered:
            self.log_buffer.append(data)
        else:
            self.send_data(
                command='log',
                data=data,
            )

    #----------------------------------------------------------------------------------------------

    def log_debug(self, *args, **kwargs):
        self.log(level=LevelDebug, *args, **kwargs)

    #----------------------------------------------------------------------------------------------

    def log_info(self, *args, **kwargs):
        self.log(level=LevelInfo, *args, **kwargs)

    #----------------------------------------------------------------------------------------------

    def log_warning(self, *args, **kwargs):
        self.log(level=LevelWarning, *args, **kwargs)

    #----------------------------------------------------------------------------------------------

    def log_error(self, *args, **kwargs):
        self.log(level=LevelError, *args, **kwargs)

    #----------------------------------------------------------------------------------------------

    def log_critical(self, *args, **kwargs):
        self.log(level=LevelCritical, *args, **kwargs)

    #----------------------------------------------------------------------------------------------

    def flush(self):
        if not self.buffered:
            return

        data = {
            'bulk_uuid': str(uuid.uuid4()),
            'items': self.log_buffer,
        }

        self.send_data(
            command='log_bulk',
            data=data,
        )

        self.log_buffer = []

    #----------------------------------------------------------------------------------------------


#**************************************************************************************************
