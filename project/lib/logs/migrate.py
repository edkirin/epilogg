from .mongo import Mongo
from project.main.models import LogEntry
import json
import uuid
import project.main.const as const


#--------------------------------------------------------------------------------------------------


def migrate_logs():
    mongo = Mongo()

    items = []

    related = [
        'client_app',
    ]
    log_entries = LogEntry.objects.select_related(*related).all()

    mongo.log.create_index('client_app')

    for log in log_entries:
        if log.format == const.FormatJson:
            try:
                data = json.loads(log.data)
            except:
                data = None
        else:
            data = log.data
        try:
            vars = json.loads(log.vars)
        except:
            vars = None

        items.append({
            'pk': uuid.uuid4(),
            'client_app': log.client_app.pk,
            'client_app_name': log.client_app.name if log.client_app is not None else None,
            'direction': log.direction,
            'level': log.level,
            'format': log.format,
            'category': log.category,
            'group': log.group,
            'bulk_uuid': log.bulk_uuid,
            'data': data,
            'vars': vars,
            'confirmed': log.confirmed,
            'timestamp': log.timestamp,
        })

    mongo.log.insert_many(items)


#--------------------------------------------------------------------------------------------------
