from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from django.db.models import Count

import uuid

from project.jinja2env import format_datetime
import project.main.const as const


#**************************************************************************************************


# automatically create rest token for new user

@receiver(post_save, sender=User)
def on_user_save(sender, **kwargs):
    if kwargs['created'] is True:
        Token(user=kwargs['instance']).save()


#**************************************************************************************************


class Facility(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    users = models.ManyToManyField(User, blank=True)
    enabled = models.BooleanField(default=True)

    class Meta:
        db_table = 'facilities'
        verbose_name_plural = "facilities"
        ordering = ['name']

    #----------------------------------------------------------------------------------------------

    def __str__(self):
        return self.name

    #----------------------------------------------------------------------------------------------


#**************************************************************************************************


class ClientApp(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_index=True)
    facility = models.ForeignKey('Facility', on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    delete_older_than = models.IntegerField(default=None, null=True, blank=True, help_text="days")
    enabled = models.BooleanField(default=True)
    entries_notset_cnt = models.PositiveIntegerField(default=0)
    entries_debug_cnt = models.PositiveIntegerField(default=0)
    entries_info_cnt = models.PositiveIntegerField(default=0)
    entries_warning_cnt = models.PositiveIntegerField(default=0)
    entries_error_cnt = models.PositiveIntegerField(default=0)
    entries_critical_cnt = models.PositiveIntegerField(default=0)
    entries_notset_unread_cnt = models.PositiveIntegerField(default=0)
    entries_debug_unread_cnt = models.PositiveIntegerField(default=0)
    entries_info_unread_cnt = models.PositiveIntegerField(default=0)
    entries_warning_unread_cnt = models.PositiveIntegerField(default=0)
    entries_error_unread_cnt = models.PositiveIntegerField(default=0)
    entries_critical_unread_cnt = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'client_apps'
        ordering = ['facility__name', 'name']

    #----------------------------------------------------------------------------------------------

    def __str__(self):
        return f"{self.facility.name} / {self.name}"

    #----------------------------------------------------------------------------------------------

    def get_entries_count(self, level):
        if level == const.LevelNotSet:
            return self.entries_notset_cnt, self.entries_notset_unread_cnt
        elif level == const.LevelDebug:
            return self.entries_debug_cnt, self.entries_debug_unread_cnt
        elif level == const.LevelInfo:
            return self.entries_info_cnt, self.entries_info_unread_cnt
        elif level == const.LevelWarning:
            return self.entries_warning_cnt, self.entries_warning_unread_cnt
        elif level == const.LevelError:
            return self.entries_error_cnt, self.entries_error_unread_cnt
        elif level == const.LevelCritical:
            return self.entries_critical_cnt, self.entries_critical_unread_cnt
        else:
            return 0, 0

    #----------------------------------------------------------------------------------------------

    def get_all_unread_entries_count(self):
        return \
            self.entries_notset_unread_cnt + \
            self.entries_debug_unread_cnt + \
            self.entries_info_unread_cnt + \
            self.entries_warning_unread_cnt + \
            self.entries_error_unread_cnt + \
            self.entries_critical_unread_cnt

    #----------------------------------------------------------------------------------------------

    def normalize_entries_cnt(self, save=True):
        self.entries_notset_cnt = 0
        self.entries_debug_cnt = 0
        self.entries_info_cnt = 0
        self.entries_warning_cnt = 0
        self.entries_error_cnt = 0
        self.entries_critical_cnt = 0
        self.entries_notset_unread_cnt = 0
        self.entries_debug_unread_cnt = 0
        self.entries_info_unread_cnt = 0
        self.entries_warning_unread_cnt = 0
        self.entries_error_unread_cnt = 0
        self.entries_critical_unread_cnt = 0

        ann = LogEntry.objects.filter(client_app=self). \
            values('level', 'confirmed'). \
            annotate(cnt=Count('level')). \
            order_by('cnt')

        for c in ann:
            if c['level'] == const.LevelNotSet:
                self.entries_notset_cnt += c['cnt']
                if not c['confirmed']:
                    self.entries_notset_unread_cnt = c['cnt']
            elif c['level'] == const.LevelDebug:
                self.entries_debug_cnt += c['cnt']
                if not c['confirmed']:
                    self.entries_debug_unread_cnt = c['cnt']
            elif c['level'] == const.LevelInfo:
                self.entries_info_cnt += c['cnt']
                if not c['confirmed']:
                    self.entries_info_unread_cnt = c['cnt']
            elif c['level'] == const.LevelWarning:
                self.entries_warning_cnt += c['cnt']
                if not c['confirmed']:
                    self.entries_warning_unread_cnt = c['cnt']
            elif c['level'] == const.LevelError:
                self.entries_error_cnt += c['cnt']
                if not c['confirmed']:
                    self.entries_error_unread_cnt = c['cnt']
            elif c['level'] == const.LevelCritical:
                self.entries_critical_cnt += c['cnt']
                if not c['confirmed']:
                    self.entries_critical_unread_cnt = c['cnt']

        if save:
            self.save()

    #----------------------------------------------------------------------------------------------


#**************************************************************************************************


class LogEntry(models.Model):
    user = models.ForeignKey(User, default=None, blank=True, null=True, on_delete=models.SET_NULL, related_name='logentry_user')
    client_app = models.ForeignKey('ClientApp', on_delete=models.CASCADE)
    direction = models.PositiveSmallIntegerField(default=const.DirectionNone, choices=const.DirectionChoices)
    level = models.PositiveSmallIntegerField(default=const.LevelNotSet, choices=const.LevelChoices)
    format = models.PositiveSmallIntegerField(default=const.FormatPlain, choices=const.FormatChoices)
    category = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    group = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    bulk_uuid = models.CharField(max_length=40, blank=True, null=True, db_index=True)
    data = models.TextField(default=None, blank=True, null=True)
    vars = models.TextField(default=None, blank=True, null=True)
    confirmed = models.BooleanField(default=False)
    timestamp = models.DateTimeField(db_index=True)

    class Meta:
        db_table = 'log_entries'
        verbose_name_plural = "Log entries"
        ordering = ['-timestamp']

    #----------------------------------------------------------------------------------------------

    def __str__(self):
        return "{timestamp} [{level}] {client_app} ({category}): {data}".format(
            timestamp=format_datetime(self.timestamp, include_seconds=True),
            level=self.get_level_display().upper(),
            client_app=self.client_app.name,
            category=self.category,
            data=self.data[:100] if self.data else "",
        )

    #----------------------------------------------------------------------------------------------

    def has_to_be_confirmed(self):
        return self.level in [const.LevelError, const.LevelCritical] and not self.confirmed

    #----------------------------------------------------------------------------------------------


#**************************************************************************************************
