from django.urls import re_path
from runtime_app.views import DynamicProxyView, health
urlpatterns=[re_path(r'^healthz$',health),re_path(r'^(?P<path>.*)$',DynamicProxyView.as_view())]
