from django.core.management.base import BaseCommand

from project.api.epilogg_client import APIClient
import project.main.const as const
import project.settings

import random
import json
import re
import time


#**************************************************************************************************


class Command(BaseCommand):
    help = ''

    #----------------------------------------------------------------------------------------------

    def log_buffered(self):
        client = APIClient(
            api_url=project.settings.local.TestClientData.api_url,
            token=project.settings.local.TestClientData.token,
            client_id=project.settings.local.TestClientData.client_id,
            buffered=True,
        )

        from project.main.models import Facility
        f = Facility.objects.get(id=1)

        print("-" * 20)
        print(str(f))
        print("-" * 20)

        for c in range(10):
            client.log(
                level=const.LevelInfo,
                data=f"Hello world {c} - {random.random()}!",
                category="Debugging",
                vars=vars(),
            )
            # time.sleep(0.1)

        client.flush()

    #----------------------------------------------------------------------------------------------

    def log_unbuffered(self):
        client = APIClient(
            api_url=project.settings.local.TestClientData.api_url,
            token=project.settings.local.TestClientData.token,
            client_id=project.settings.local.TestClientData.client_id,
            buffered=False,
        )

        from project.main.models import Facility
        f = Facility.objects.get(id=1)

        print("-" * 20)
        print(str(f))
        print("-" * 20)

        # client.log(
        #     level=const.LevelInfo,
        #     direction=const.DirectionRequest,
        #     data=f"Hello world!",
        #     category="Debugging",
        #     vars=vars(),
        # )

        data = {
            'first_field': "This is first field",
            'second_field': "This is second field",
            'int_field': 12345,
            'float_field': 3.14,
        }

        random_level = list(dict(const.LevelChoices).keys())[random.randint(0, len(const.LevelChoices) - 1)]

        client.log(
            level=random_level,
            direction=const.DirectionResponse,
            data=data,
            format=const.FormatJson,
            category="Debugging",
            vars=vars(),
        )

    #----------------------------------------------------------------------------------------------

    def convert_log(self):
        fname = '/home/eden/www/ticketshop.hr/data/log/websockets_api.log'

        levels = [
            const.LevelDebug, const.LevelInfo, const.LevelWarning, const.LevelError, const.LevelCritical
        ]
        categories = [
            'Debug', 'Production', 'Category 1', 'Category 2', 'Category 3',
        ]

        client = APIClient(
            api_url=project.settings.local.TestClientData.api_url,
            token=project.settings.local.TestClientData.token,
            client_id=project.settings.local.TestClientData.client_id,
            buffered=False,
        )

        with open(fname, 'r') as f:
            for n, line in enumerate(f):
                line = line.strip()
                if len(line):
                    level = levels[random.randint(0, len(levels) - 1)]
                    category = categories[random.randint(0, len(categories) - 1)]

                    client.log(
                        level=level,
                        data=line[60:],
                        format=const.FormatPlain,
                        category=category,
                        vars=vars(),
                    )

    #----------------------------------------------------------------------------------------------

    def convert_fufis_log(self):
        fname = '/tmp/fufis.log'

        client = APIClient(
            api_url=project.settings.local.TestClientData.api_url,
            token=project.settings.local.TestClientData.token,
            client_id=project.settings.local.TestClientData.client_id,
            buffered=False,
        )

        pattern = r'^(\w+): ([a-zA-Z\s]+): (.*)$'

        with open(fname, 'r') as f:
            for n, line in enumerate(f):
                line = line[25:].strip()

                m = re.match(pattern, line, re.MULTILINE)
                level = m.group(1)
                direction = m.group(2)
                data = json.loads(m.group(3))

                client.log(
                    level=const.LevelError if level == "ERROR" else const.LevelInfo,
                    direction=const.DirectionRequest if direction == "Request params" else const.DirectionResponse,
                    data=data,
                    format=const.FormatJson,
                    category="API",
                )

    #----------------------------------------------------------------------------------------------

    def handle(self, *args, **options):
        # self.log_buffered()
        self.log_unbuffered()
        # self.convert_log()
        # self.convert_fufis_log()

    #----------------------------------------------------------------------------------------------


#**************************************************************************************************
