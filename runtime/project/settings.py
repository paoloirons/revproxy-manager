import os
SECRET_KEY='runtime-not-used-for-auth'
DEBUG=False
ALLOWED_HOSTS=['*']
ROOT_URLCONF='project.urls'
MIDDLEWARE=[]
INSTALLED_APPS=['revproxy.apps.RevProxyConfig']
USE_TZ=True
DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'
