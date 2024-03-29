import logging
import uuid
from typing import List

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from django.db.models import Q
from django.template.loader import render_to_string

import json

import project.settings
from project.main.models import ClientApp, LogEntry
from project.jinja2env import format_datetime


logger = logging.getLogger("websockets")


#**************************************************************************************************


async def on_log_event_occurred(client_app_id: str, log_items: List[LogEntry]):
    logger.info(f"[{client_app_id}] Log event: {log_items}")
    channel_layer = get_channel_layer()

    data = {
        'event': 'log_event_occurred',
        'log': {
            'items': [
                {
                    'id': c.id,
                    'direction': c.direction,
                    'direction_str': c.get_direction_display(),
                    'level': c.level,
                    'level_str': c.get_level_display(),
                    'format': c.format,
                    'format_str': c.get_format_display(),
                    'category': c.category,
                    'group': c.group,
                    'data': c.data,
                    'vars': c.vars,
                    'timestamp': format_datetime(c.timestamp),
                    'row_html': render_to_string('consumers/log_entry_log.html', {
                        'item': c,
                        'show_client_app_col': True,
                        'client_app_name': c.client_app.name if c.client_app is not None else "",
                    })
                } for c in log_items[::-1]  # set items in reverse order
            ]
        },
    }

    logger.info(f"Sending notify_for_log_event: {data}")
    await channel_layer.group_send(
        group=str(client_app_id),
        message={
            "type": "notify_for_log_event",
            "data": data,
        },
    )


#----------------------------------------------------------------------------------------------


def debug_print(*args):
    if project.settings.local.Debug:
        print(*args)


#**************************************************************************************************


class OnLogEventConsumer(AsyncWebsocketConsumer):
    user = None
    client_apps = None
    filter_level = None
    filter_category = None

    #----------------------------------------------------------------------------------------------

    async def connect(self):
        debug_print(">>> CONNECT", self.channel_name)
        logger.info(f"Client connected to channel {self.channel_name}")

        self.client_apps = dict()

        if 'user' in self.scope and self.scope['user'] is not None:
            self.user = self.scope['user']
            await self.accept()

    #----------------------------------------------------------------------------------------------

    async def disconnect(self, close_code):
        logger.info(f"Client disconnected from channel {self.channel_name}")
        await self.unsubscribe_from_client_app_groups()
        debug_print(">>> DISCONNECT", self.channel_name)

    #----------------------------------------------------------------------------------------------

    async def receive(self, text_data=None, bytes_data=None):
        logger.info(f"Client received data: {text_data}")
        try:
            data = json.loads(text_data)
        except:
            logger.error(f"Error decoding data to json: {text_data}")
            data = None

        debug_print(">>> RECEIVE")
        debug_print(data)

        if data is not None:
            if 'cmd' in data:
                cmd = data['cmd']

                if cmd == 'watch_client_app':
                    if 'client_app_id' in data:
                        client_app_id = data['client_app_id']
                        self.filter_level = data['filter_level'] if 'filter_level' in data else None
                        self.filter_category = data['filter_category'] if 'filter_category' in data else None
                        await self.get_client_app(client_app_id)
                        await self.subscribe_to_client_app_groups()

                elif cmd == 'watch_facility':
                    if 'facility_id' in data:
                        facility_id = data['facility_id']
                        self.filter_level = data['filter_level'] if 'filter_level' in data else None
                        self.filter_category = data['filter_category'] if 'filter_category' in data else None
                        await self.get_client_apps_from_facility(facility_id)
                        await self.subscribe_to_client_app_groups()

                elif cmd == 'watch_all':
                    await self.get_all_client_apps()
                    await self.subscribe_to_client_app_groups()

                else:
                    # err: unknown command
                    pass
            else:
                # err: invalid format
                pass
        else:
            # err: invalid json format
            pass

    #----------------------------------------------------------------------------------------------

    @database_sync_to_async
    def get_client_app(self, client_app_id):
        q = Q(id=client_app_id) & \
            Q(facility__users=self.user)

        try:
            client_app = ClientApp.objects.get(q)
        except ClientApp.DoesNotExist:
            client_app = None

        if client_app is not None:
            self.client_apps = {
                str(client_app.id): client_app,
            }

        return client_app is not None

    #----------------------------------------------------------------------------------------------

    @database_sync_to_async
    def get_client_apps_from_facility(self, facility_id):
        q = Q(facility=facility_id) & \
            Q(facility__users=self.user)

        client_apps = ClientApp.objects.filter(q)

        self.client_apps = {
            str(c.id): c for c in client_apps
        }

        return len(self.client_apps) > 0

    #----------------------------------------------------------------------------------------------

    @database_sync_to_async
    def get_all_client_apps(self):
        q = Q(facility__users=self.user)

        client_apps = ClientApp.objects.filter(q)

        self.client_apps = {
            str(c.id): c for c in client_apps
        }

        return len(self.client_apps) > 0

    #----------------------------------------------------------------------------------------------

    async def subscribe_to_client_app_groups(self):
        await self.unsubscribe_from_client_app_groups()

        for client_app_id in self.client_apps:
            debug_print(">>> subscribed to", client_app_id, self.channel_name)
            logger.info(f"[{client_app_id}] Subscribe to channel: {self.channel_name}")
            await self.channel_layer.group_add(
                group=client_app_id,
                channel=self.channel_name,
            )

    #----------------------------------------------------------------------------------------------

    async def unsubscribe_from_client_app_groups(self):
        for client_app_id in self.client_apps:
            logger.info(f"[{client_app_id}] Unsubscribe from channel: {self.channel_name}")
            await self.channel_layer.group_discard(
                group=client_app_id,
                channel=self.channel_name,
            )

    #----------------------------------------------------------------------------------------------

    async def notify_for_log_event(self, event):
        data = event['data']

        # do the filtering only if any filter is set
        if self.filter_level is not None or self.filter_category is not None:
            filtered_log = []
            for c in data['log']['items']:
                level_ok = self.filter_level in [None, c['level']]
                category_ok = self.filter_category in [None, c['category']]

                if level_ok and category_ok:
                    filtered_log.append(c)
            data['log']['items'] = filtered_log

        await self.send(text_data=json.dumps(data))

    #----------------------------------------------------------------------------------------------


#**************************************************************************************************
