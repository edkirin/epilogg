from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render
from django.contrib import auth
from django.template.loader import render_to_string
from django.db.models import Q
from django.contrib.auth.decorators import login_required

import project.main.const as const
from .models import ClientApp
from project.lib.logs import Mongo


"""
    Bootstrap admin: https://adminlte.io/
"""


#--------------------------------------------------------------------------------------------------


def create_sidebar_data(user, selected_facility=None, selected_client_app=None):
    q = Q(facility__users=user) & \
        Q(facility__enabled=True) & \
        Q(enabled=True)

    related = [
        'facility',
    ]
    client_apps = list(ClientApp.objects.select_related(*related).filter(q))

    facilities = []

    for app in client_apps:
        d = None
        for f in facilities:
            if f['facility'].id == app.facility.id:
                d = f
                break

        if d is None:
            d = {
                'facility': app.facility,
                'active': selected_facility.id == app.facility.id if selected_facility is not None else None,
                'apps': [],
            }
            facilities.append(d)

        d['apps'].append({
            'item': app,
            'unseen_entries': app.get_all_unread_entries_count(),
            'unseen_error_entries': app.get_entries_count(const.LevelError)[1] + app.get_entries_count(const.LevelCritical)[1],
        })

    return {
        'apps': client_apps,
        'facilities': facilities,
        'selected_facility_id': selected_facility.id if selected_facility is not None else None,
        'selected_client_app': selected_client_app.id if selected_client_app is not None else None,
    }


#--------------------------------------------------------------------------------------------------


@login_required
def frontpage(request):
    if request.method == 'POST':
        cmd = request.POST.get('cmd')

        if cmd == 'mark_log_seen':
            app_id = request.POST.get('app_id')
            q = Q(facility__users=request.user) & \
                Q(id=app_id)

            ClientApp.objects.filter(q).update(
                entries_notset_unread_cnt=0,
                entries_debug_unread_cnt=0,
                entries_info_unread_cnt=0,
                entries_warning_unread_cnt=0,
                entries_error_unread_cnt=0,
                entries_critical_unread_cnt=0,
            )

            mongo = Mongo()
            f = {
                'client_app': app_id,
                'confirmed': False,
            }
            mongo.log.update_many(
                filter=f,
                update={
                    '$set': {
                        'confirmed': True,
                    }
                }
            )

            return HttpResponseRedirect(request.POST.get('backlink'))

    sidebar_data = create_sidebar_data(
        user=request.user,
    )

    stats = {
        'facilities': [],
    }

    for app in sidebar_data['apps']:
        d = None
        for f in stats['facilities']:
            if app.facility_id == f['item'].id:
                d = f
                break

        if d is None:
            d = {
                'item': app.facility,
                'apps': [],
            }
            stats['facilities'].append(d)

        d['apps'].append(app)

    return render(request, 'frontpage.html', {
        'sidebar_data': sidebar_data,
        'hide_breadcrumbs': True,
    })


#--------------------------------------------------------------------------------------------------
