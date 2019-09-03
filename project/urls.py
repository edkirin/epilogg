from django.conf.urls import include, url
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views

import project.settings
import project.main.views
import project.main.entries
import project.main.user
import project.api.urls


#**************************************************************************************************


urlpatterns = [
    path('', project.main.views.frontpage),
    path('facility/<int:facility_id>/', project.main.entries.entry_list),
    path('facility/<int:facility_id>/app/<slug:client_app_id>/', project.main.entries.entry_list),
    path('get_log_entry_details/', project.main.entries.get_log_entry_details),

    path('admin/', admin.site.urls),
    path('api/', include(project.api.urls)),
    path('accounts/login/', auth_views.LoginView.as_view()),
    path('user/login/', project.main.user.login),
]


if not project.settings.local.Deploy:
    from django.conf.urls.static import static
    urlpatterns += static(project.settings.MEDIA_URL, document_root=project.settings.MEDIA_ROOT)
    urlpatterns += static(project.settings.STATIC_SERVE_URL, document_root=project.settings.STATIC_SERVE_ROOT)

    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
        # url(r'^404/?$', views.handle_404),
        # url(r'^500/?$', views.handle_500),
    ]


# create css version timestamp on first request
import time
timestamp = '%d' % (int(time.mktime(time.gmtime())))
fname = '%s/timestamp.inc' % (project.settings.TEMPLATES[0]['DIRS'][0])
with open(fname, 'w') as f:
    f.write(timestamp)
