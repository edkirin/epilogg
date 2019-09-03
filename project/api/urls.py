from django.contrib import admin
from django.urls import path

import project.main.views
import project.api.views as views



urlpatterns = [
    path('', views.DispatchView.as_view(), name='dispatch'),
    path('hello/', views.HelloWorldView.as_view(), name='hello'),
]
