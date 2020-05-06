from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render
from django.db.models import Q
from django.contrib.auth.decorators import login_required

import json
import yaml
import uuid
import pymongo

from .models import Facility, ClientApp
import project.main.const as const
from .util import str_to_int
from .views import create_sidebar_data
import project.settings
from project.lib.logs import Mongo


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

    all_client_apps = ClientApp.objects.filter(facility=facility)
    all_client_apps_ids = [c.id for c in all_client_apps]

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
        f_common = {
            'client_app': {
                '$in': all_client_apps_ids,
            },
        }
    else:
        f_common = {
            'client_app': client_app.pk,
        }

    active_filter = get_list_filters(request, facility=facility, client_app=client_app)

    f = f_common.copy()
    if 'category' in active_filter and active_filter['category'] is not None:
        f.update({
            'category': active_filter['category'],
        })

    if 'level' in active_filter and active_filter['level'] is not None:
        f.update({
            'level': active_filter['level'],
        })

    # if 'search' in active_filter and active_filter['search']:
    #     terms = [c.strip() for c in active_filter['search'].split(' ') if len(c)]
    #     for term in terms:
    #         q &= Q(data__icontains=term)

    mongo = Mongo()
    items = mongo.log.find(f).sort('timestamp', direction=pymongo.DESCENDING)

    sidebar_data = create_sidebar_data(
        user=request.user,
        selected_facility=facility,
        selected_client_app=client_app,
    )

    # get all categories
    categories = mongo.log.aggregate([
        {
            '$match': f_common,
        },
        {
            '$group': {
                '_id': "$category",
                'total': {
                    '$sum': 1,
                },
            },
        },
    ])

    filter = {
        'categories': [c['_id'] for c in categories if c['_id']],
        'search': active_filter['search'] if 'search' in active_filter else "",
        'selected_category': active_filter['category'] if 'category' in active_filter else None,
        'selected_level': active_filter['level'] if  'level' in active_filter else None,
    }

    if client_app is None:
        client_apps_data = {
            c.id: c.name for c in all_client_apps
        }
    else:
        client_apps_data = dict()

    def get_client_app_name(id):
        return client_apps_data[id] if id in client_apps_data else ""

    return render(request, 'entries/list.html', {
        'items': items,
        'facility': facility,
        'client_app': client_app,
        'sidebar_data': sidebar_data,
        'filter': filter,
        'get_client_app_name': get_client_app_name,
        'settings': project.settings,
        'current_page': current_page,
    })


#--------------------------------------------------------------------------------------------------


@login_required
def get_log_entry_details(request):
    f = {
        'pk': uuid.UUID(request.POST.get('id')),
    }

    mongo = Mongo()
    item = mongo.log.find_one(f)

    if item is None:
        raise Http404

    q = Q(pk=item['client_app']) & \
        Q(facility__users=request.user)

    try:
        app = ClientApp.objects.get(q)
    except ClientApp.DoesNotExist:
        raise Http404

    # always add plain data
    data = {
        'formats': ['plain'],
        'plain': str(item['data']),
    }

    force_unicode = True

    if item['format'] == const.FormatJson:
        try:
            json_data = item['data']

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
    if item['vars']:
        try:
            vars = yaml.dump(item['vars'], default_flow_style=False)
            # vars = json.dumps(json.loads(item.vars), sort_keys=True, indent=4, separators=(',', ': '))
        except:
            pass
    if len(vars):
        data['formats'].append('vars')

    res = mongo.normalize_log_entry(
        item=item,
        app=app,
        data=data,
        vars=vars,
    )

    return HttpResponse(json.dumps(res), content_type="application/json")


#--------------------------------------------------------------------------------------------------
