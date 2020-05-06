from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated

import datetime
import uuid

from django.db.models import Q, F
from django.core.exceptions import ValidationError

from project.main.models import ClientApp
from project.main.util import str_to_int
import project.main.const as const
import project.settings
from project.lib.logs import Mongo

if project.settings.local.ChannelsEnabled:
    from project.main.consumers import on_log_event_occurred
    from asgiref.sync import async_to_sync


#**************************************************************************************************


VALID_LEVELS = (
    const.LevelNotSet,
    const.LevelDebug,
    const.LevelInfo,
    const.LevelWarning,
    const.LevelError,
    const.LevelCritical,
)


class EntryCounter:
    client_app = None
    levels = None

    #----------------------------------------------------------------------------------------------

    def __init__(self, client_app):
        self.client_app = client_app
        self.levels = {
            c: 0 for c in VALID_LEVELS
        }

    #----------------------------------------------------------------------------------------------

    def add(self, level, cnt=1):
        if level in self.levels:
            self.levels[level] += cnt

    #----------------------------------------------------------------------------------------------

    def write(self):
        update_fields = dict()

        def add_field(cnt, v1, v2):
            if cnt > 0:
                update_fields.update({
                    v1: F(v1) + cnt,
                    v2: F(v2) + cnt,
                })

        add_field(self.levels[const.LevelNotSet], 'entries_notset_cnt', 'entries_notset_unread_cnt')
        add_field(self.levels[const.LevelDebug], 'entries_debug_cnt', 'entries_debug_unread_cnt')
        add_field(self.levels[const.LevelInfo], 'entries_info_cnt', 'entries_info_unread_cnt')
        add_field(self.levels[const.LevelWarning], 'entries_warning_cnt', 'entries_warning_unread_cnt')
        add_field(self.levels[const.LevelError], 'entries_error_cnt', 'entries_error_unread_cnt')
        add_field(self.levels[const.LevelCritical], 'entries_critical_cnt', 'entries_critical_unread_cnt')

        if update_fields:
            ClientApp.objects.filter(id=self.client_app.id).update(
                **update_fields
            )

    #----------------------------------------------------------------------------------------------


#**************************************************************************************************


class HelloWorldView(APIView):
    # permission_classes = (IsAuthenticated,)

    def post(self, request):
        content = {
            'message': 'Hello, World!'
        }
        return Response(content)


#**************************************************************************************************


class DispatchView(APIView):
    permission_classes = (IsAuthenticated,)
    mongo = None

    #----------------------------------------------------------------------------------------------

    def get_client_from_request(self, request):
        if 'client_id' not in request.data:
            raise APIException("Client ID required")

        q = Q(id=request.data['client_id']) & \
            Q(enabled=True)

        try:
            return ClientApp.objects.get(q)
        except (ClientApp.DoesNotExist, ValidationError):
            raise APIException("Invalid client_id")

    #----------------------------------------------------------------------------------------------

    def __create_entry(self, client_app, data, counter, bulk_uuid=None):
        if 'level' not in data:
            raise APIException("Invalid parameter")
        if 'format' not in data:
            raise APIException("Invalid parameter")

        direction = str_to_int(data['direction'], default=const.DirectionNone) if 'direction' in data else const.DirectionNone
        if not direction in const.ValidDirections:
            direction = const.DirectionNone

        try:
            level = int(data['level'])
            format = int(data['format'])
        except ValueError:
            raise APIException("Invalid parameter")

        timestamp = None
        if 'timestamp' in data:
            try:
                timestamp = datetime.datetime.strptime(data['timestamp'], "%Y-%m-%d %H:%M:%S.%f")
            except:
                pass

        counter.add(level=level, cnt=1)

        return {
            'pk': uuid.uuid4(),
            'client_app': client_app.pk,
            'client_app_name': client_app.name if client_app is not None else None,
            'direction': direction,
            'level': level,
            'format': format,
            'category': data['category'] if 'category' in data else None,
            'group': data['group'] if 'group' in data else None,
            'bulk_uuid': bulk_uuid,
            'data': data['data'],
            'vars': data['variables'] if 'variables' in data else None,
            'confirmed': False,
            'timestamp': timestamp if timestamp is not None else datetime.datetime.now(),
        }

    #----------------------------------------------------------------------------------------------

    def cmd_log(self, client_app, data):
        counter = EntryCounter(client_app)

        entry = self.__create_entry(
            client_app=client_app,
            data=data,
            counter=counter,
        )
        self.mongo.log.insert(entry)

        counter.write()

        if project.settings.local.ChannelsEnabled:
            async_to_sync(on_log_event_occurred)(
                client_app=client_app,
                log_items=[entry],
            )

        return {
            'success': True,
        }

    #----------------------------------------------------------------------------------------------

    def cmd_log_bulk(self, client_app, data):
        if 'items' not in data:
            raise APIException("Invalid parameter")

        bulk = []
        bulk_uuid = data['bulk_uuid'] if 'bulk_uuid' in data else None
        counter = EntryCounter(client_app)

        for item in data['items']:
            entry = self.__create_entry(
                client_app=client_app,
                data=item,
                counter=counter,
                bulk_uuid=bulk_uuid,
            )
            bulk.append(entry)

        if len(bulk):
            self.mongo.log.insert_many(bulk)

        counter.write()

        if bulk and project.settings.local.ChannelsEnabled:
            async_to_sync(on_log_event_occurred)(
                client_app=client_app,
                log_items=bulk,
            )

        return {
            'success': True,
        }

    #----------------------------------------------------------------------------------------------

    def post(self, request):
        self.mongo = Mongo()
        client_app = self.get_client_from_request(request)

        if 'command' not in request.data:
            raise APIException("Invalid command")

        if request.data['command'] == 'log':
            res = self.cmd_log(client_app=client_app, data=request.data)

        elif request.data['command'] == 'log_bulk':
            res = self.cmd_log_bulk(client_app=client_app, data=request.data)

        else:
            raise APIException("Invalid command")

        return Response(res)

    #----------------------------------------------------------------------------------------------


#**************************************************************************************************
