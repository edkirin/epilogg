from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render
from django.contrib import auth
from django.template.loader import render_to_string
from django.db.models import Q, Count
from django.contrib.auth.decorators import login_required

import json
import yaml

from .models import Facility, ClientApp, LogEntry
import project.main.const as const
from project.jinja2env import format_datetime
from .util import str_to_int
from .views import create_sidebar_data
import project.settings


#--------------------------------------------------------------------------------------------------


def create_filter_key(facility, client_app):
    return 'log_entry_filters_{facility_id}-{app_id}'.format(
        facility_id=facility.id if facility is not None else 0,
        app_id=client_app.id if client_app is not None else 0,
    )


#--------------------------------------------------------------------------------------------------


def set_list_filters(request, facility, client_app):
    key_name = create_filter_key(facility, client_app)

    filter_category = request.POST.get('filter_category', "").strip()

    request.session[key_name] = {
        'search': request.POST.get('filter_search', "").strip(),
        'level': str_to_int(request.POST.get('filter_level'), default=None),
        'category': filter_category if len(filter_category) else None,
    }
    request.session.modified = True


#--------------------------------------------------------------------------------------------------


def get_list_filters(request, facility, client_app):
    key_name = create_filter_key(facility, client_app)

    if key_name in request.session:
        filters = request.session[key_name]
        filter_search = filters['search'] if 'search' in filters else None
        filter_level = filters['level'] if 'level' in filters else None
        filter_category = filters['category'] if 'category' in filters else None
    else:
        filter_search = filter_level = filter_category = None

    return {
        'search': filter_search,
        'level': filter_level,
        'category': filter_category,
    }


#--------------------------------------------------------------------------------------------------


def clear_list_filters(request, facility, client_app):
    key_name = create_filter_key(facility, client_app)

    if key_name in request.session:
        del request.session[key_name]
        request.session.modified = True


#--------------------------------------------------------------------------------------------------


@login_required
def entry_list(request, facility_id, client_app_id=None):
    q = Q(id=facility_id) & \
        Q(users=request.user) & \
        Q(enabled=True)

    try:
        facility = Facility.objects.get(q)
    except Facility.DoesNotExist:
        raise Http404

    # locate_entry = request.GET.get('locate_entry', default=None)

    if client_app_id is not None:
        q = Q(id=client_app_id) & \
            Q(facility=facility) & \
            Q(enabled=True)
        try:
            client_app = ClientApp.objects.get(q)
        except ClientApp.DoesNotExist:
            raise Http404
    else:
        client_app = None

    current_page = int(request.GET.get('page', 1))

    if request.method == 'POST':
        cmd = request.POST.get('cmd')

        if cmd == 'set_filter':
            set_list_filters(request, facility=facility, client_app=client_app)
            return HttpResponseRedirect(request.path)

        elif cmd == 'clear_filter':
            clear_list_filters(request, facility=facility, client_app=client_app)
            return HttpResponseRedirect(request.path)

        else:
            raise Http404

    if client_app is None:
        q_common = Q(client_app__facility=facility)
    else:
        q_common = Q(client_app=client_app)

    active_filter = get_list_filters(request, facility=facility, client_app=client_app)

    q = Q() & q_common
    if 'category' in active_filter and active_filter['category'] is not None:
        q &= Q(category=active_filter['category'])

    if 'level' in active_filter and active_filter['level'] is not None:
        q &= Q(level=active_filter['level'])

    if 'search' in active_filter and active_filter['search']:
        terms = [c.strip() for c in active_filter['search'].split(' ') if len(c)]
        for term in terms:
            q &= Q(data__icontains=term)

    related = [
    ]
    only = [
        'format', 'level', 'timestamp', 'category', 'direction', 'data',
    ]

    if client_app is None:
        related += [
            'client_app',
        ]
        only += [
            'client_app__name',
        ]

    items = LogEntry.objects.only(*only).filter(q)
    if len(related):
        items = items.select_related(*related)

    sidebar_data = create_sidebar_data(
        user=request.user,
        selected_facility=facility,
        selected_client_app=client_app,
    )

    # get all categories
    ann = LogEntry.objects.filter(q_common). \
        values('category'). \
        annotate(cnt=Count('category')). \
        order_by('category')

    filter = {
        'categories': [c['category'] for c in ann if c['category']],
        'search': active_filter['search'] if 'search' in active_filter else "",
        'selected_category': active_filter['category'] if 'category' in active_filter else None,
        'selected_level': active_filter['level'] if  'level' in active_filter else None,
    }

    return render(request, 'entries/list.html', {
        'items': items,
        'facility': facility,
        'client_app': client_app,
        'sidebar_data': sidebar_data,
        'filter': filter,
        'settings': project.settings,
        'current_page': current_page,
    })


#--------------------------------------------------------------------------------------------------


@login_required
def get_log_entry_details(request):
    q = Q(id=request.POST.get('id')) & \
        Q(client_app__facility__users=request.user)

    related = [
        'client_app',
    ]

    try:
        item = LogEntry.objects.select_related(*related).get(q)
    except (LogEntry.DoesNotExist, ValueError):
        raise Http404

    # always add plain data
    data = {
        'formats': ['plain'],
        'plain': item.data,
    }

    force_unicode = True

    if item.format == const.FormatJson:
        try:
            json_data = json.loads(item.data)

            # decode json
            data.update({
                'json': json.dumps(
                    json_data,
                    sort_keys=True,
                    indent=4,
                    separators=(',', ': '),
                    ensure_ascii=not force_unicode,
                ),
            })
            data['formats'].append('json')
            # add yaml from json too
            data.update({
                'yaml': yaml.dump(
                    json_data,
                    default_flow_style=False,
                    allow_unicode=force_unicode
                ),
            })
            data['formats'].append('yaml')
        except:
            pass

    vars = ""
    if item.vars:
        try:
            vars = yaml.dump(json.loads(item.vars), default_flow_style=False)
            # vars = json.dumps(json.loads(item.vars), sort_keys=True, indent=4, separators=(',', ': '))
        except:
            pass
    if len(vars):
        data['formats'].append('vars')

    res = {
        'id': item.id,
        'client_app': item.client_app.name,
        'timestamp': format_datetime(item.timestamp, include_seconds=True),
        'level': item.level,
        'level_str': item.get_level_display(),
        'level_label_class': const.LevelLabelClass[item.level],
        'format': item.format,
        'format_str': item.get_format_display(),
        'category': item.category,
        'data': data,
        'vars': vars,
        'direction': item.direction,
        'direction_str': item.get_direction_display(),
        'direction_label_class': const.DirectionLabelClass[item.direction],
    }

    return HttpResponse(json.dumps(res), content_type="application/json")


#--------------------------------------------------------------------------------------------------
