from django.core.management.base import BaseCommand
from django.db.models import Q

import datetime

from project.main.models import ClientApp, LogEntry


#**************************************************************************************************


class Command(BaseCommand):
    help = ''

    #----------------------------------------------------------------------------------------------

    def handle(self, *args, **options):
        q = ~Q(delete_older_than=None)

        for app in ClientApp.objects.filter(q):
            threshold = datetime.datetime.now() - datetime.timedelta(days=app.delete_older_than)
            LogEntry.objects.filter(client_app=app, timestamp__lte=threshold).delete()
            app.normalize_entries_cnt()

    #----------------------------------------------------------------------------------------------


#**************************************************************************************************
