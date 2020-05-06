from pymongo import MongoClient

import project.settings
from project.jinja2env import format_datetime, entry_level_display, entry_direction_display, entry_format_display
import project.main.const as const


#**************************************************************************************************


class Mongo:
    client: MongoClient = None
    db = None
    log = None

    #----------------------------------------------------------------------------------------------

    def __init__(self):
        self.client = MongoClient(project.settings.local.MONGO_CLIENT)
        self.db = self.client[project.settings.local.MONGO_LOGS_DB]
        self.log = self.db[project.settings.local.MONGO_LOGS_COLLECTION]

    #----------------------------------------------------------------------------------------------

    @staticmethod
    def normalize_log_entry(item, app, data=None, vars=None):
        return {
            'id': str(item['pk']),
            'client_app': app.name if app is not None else None,
            'timestamp': format_datetime(item['timestamp'], include_seconds=True),
            'level': item['level'],
            'level_str': entry_level_display(item['level']),
            'level_label_class': const.LevelLabelClass[item['level']],
            'format': item['format'],
            'format_str': entry_format_display(item['format']),
            'category': item['category'],
            'data': data if data is not None else item['data'],
            'vars': vars if vars is not None else item['vars'],
            'direction': item['direction'],
            'direction_str': entry_direction_display(item['direction']),
            'direction_label_class': const.DirectionLabelClass[item['direction']],
        }

    #----------------------------------------------------------------------------------------------


#**************************************************************************************************
