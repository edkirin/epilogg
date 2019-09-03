from django.contrib import admin
from .models import *


#--------------------------------------------------------------------------------------------------


class ClientAppAdmin(admin.ModelAdmin):
    readonly_fields = [
        'id',
        'entries_notset_cnt',
        'entries_debug_cnt',
        'entries_info_cnt',
        'entries_warning_cnt',
        'entries_error_cnt',
        'entries_critical_cnt',
        'entries_notset_unread_cnt',
        'entries_debug_unread_cnt',
        'entries_info_unread_cnt',
        'entries_warning_unread_cnt',
        'entries_error_unread_cnt',
        'entries_critical_unread_cnt',
    ]


#--------------------------------------------------------------------------------------------------


admin.site.register(Facility)
admin.site.register(ClientApp, ClientAppAdmin)
admin.site.register(LogEntry)
