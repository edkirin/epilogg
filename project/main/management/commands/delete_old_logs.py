from django.core.management.base import BaseCommand
from django.db.models import Q

import datetime

from project.main.models import ClientApp
from project.lib.logs import Mongo


#**************************************************************************************************


class Command(BaseCommand):
    help = ''

    #----------------------------------------------------------------------------------------------

    def handle(self, *args, **options):
        mongo = Mongo()
        q = ~Q(delete_older_than=None)

        for app in ClientApp.objects.filter(q):
            threshold = datetime.datetime.now() - datetime.timedelta(days=app.delete_older_than)

            mongo.log.delete_many({
                'client_app': app.pk,
                'timestamp': {
                    '$lt': threshold,
                }
            })

            app.normalize_entries_cnt()

    #----------------------------------------------------------------------------------------------


#**************************************************************************************************
