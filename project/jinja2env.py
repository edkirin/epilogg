from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse
from django.db.models import Q

import datetime

from jinja2 import Environment
import project.settings


#--------------------------------------------------------------------------------------------------


def get_site_name():
    return project.settings.SiteName


#--------------------------------------------------------------------------------------------------


def get_const_module():
    import project.main.const
    return project.main.const


#--------------------------------------------------------------------------------------------------


def slugify(text):
    from django.template.defaultfilters import slugify
    return slugify(text)


#--------------------------------------------------------------------------------------------------


def format_float(value, precision=0, thousands=False, default='0'):
    try:
        if thousands:
            return "{:,.2f}".format(value)
        if precision != 0:
            precison_str = "%%.%df" % precision
            return precison_str % value
        else:
            return "%g" % value
    except:
        return default


#--------------------------------------------------------------------------------------------------


def format_float_thousands(value, precision=0):
    return format_float(value, precision=precision, thousands=True)


#--------------------------------------------------------------------------------------------------


def format_int_thousands(value):
    return "{:,}".format(value)


#--------------------------------------------------------------------------------------------------


def format_datetime(value, format='%d.%m.%Y %H:%M', include_seconds=False, default='-'):
    try:
        if include_seconds:
            format = '%d.%m.%Y %H:%M:%S'
        return value.strftime(format)
    except (AttributeError, ValueError):
        return default


#--------------------------------------------------------------------------------------------------


def format_compact_datetime(value, include_seconds=False):
    if value is None:
        return '-'

    if (datetime.datetime.now() - value).days < 1:
        format = '%H:%M:%S' if include_seconds else '%H:%M'
    else:
        format = '%d.%m.%Y %H:%M:%S' if include_seconds else '%d.%m.%Y %H:%M'

    return format_datetime(value, format=format)


#--------------------------------------------------------------------------------------------------


def format_date(value, format="%d.%m.%Y", default="-"):
    return format_datetime(value, format=format, default=default)


#--------------------------------------------------------------------------------------------------


def format_time(value, format="%H:%M"):
    return format_datetime(value, format=format)

#--------------------------------------------------------------------------------------------------


def format_weekday(value):
    from django.utils.translation import ugettext as _
    try:
        return [_("Nedjelja"), _("Ponedjeljak"), _("Utorak"), _("Srijeda"), _(u"Četvrtak"), _("Petak"), _("Subota")][int(value.strftime("%w"))]
    except (AttributeError, ValueError):
        return "-"


#--------------------------------------------------------------------------------------------------


def format_weekday_date(value):
    return "%s, %s" % (format_weekday(value), format_date(value))


#--------------------------------------------------------------------------------------------------


def urlencode(value):
    from django.template.defaultfilters import urlencode
    return urlencode(value)


#--------------------------------------------------------------------------------------------------


def ago(seconds):
    from project.lib.ago import human
    return human(
        subject=datetime.timedelta(seconds=seconds),
        past_tense='{}',
        future_tense='{}',
    )


#--------------------------------------------------------------------------------------------------


def get_year_today():
    return datetime.date.today().year


#--------------------------------------------------------------------------------------------------


def environment(**options):
    from django.utils.translation import ugettext

    env = Environment(**options)
    env.add_extension('project.main.middleware.pagination.AutopaginateExtension')
    env.globals.update({
        'static': staticfiles_storage.url,
        'url': reverse,
        'get_site_name': get_site_name,
        'get_const_module': get_const_module,
        'slugify': slugify,
        'format_float': format_float,
        'format_float_thousands': format_float_thousands,
        'format_int_thousands': format_int_thousands,
        'format_datetime': format_datetime,
        'format_date': format_date,
        'format_time': format_time,
        'format_weekday': format_weekday,
        'format_weekday_date': format_weekday_date,
        'gettext': ugettext,
        'urlencode': urlencode,
        'ago': ago,
        'format_compact_datetime': format_compact_datetime,
        'get_year_today': get_year_today,
        'is_deploy': lambda: project.settings.local.Deploy,
        'is_debug': lambda: project.settings.local.Debug,
        'channels_enabled': lambda: project.settings.local.ChannelsEnabled,
    })
    return env


#--------------------------------------------------------------------------------------------------
