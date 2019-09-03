from django.conf.urls import url

from . import consumers

websocket_urlpatterns = [
    url(r'^ws/on_log_event/$', consumers.OnLogEventConsumer),
]
