"""MRMBackend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from MRMBackend import settings
import app.views

urlpatterns = [
    path(settings.URL_PREFIX + 'admin/', admin.site.urls),
    path(settings.URL_PREFIX + 'api/upload', app.views.upload),
    path(settings.URL_PREFIX + 'api/generate', app.views.generate),
    path(settings.URL_PREFIX + 'api/query', app.views.query),
    path(settings.URL_PREFIX + 'api/download', app.views.download),
    path(settings.URL_PREFIX + 'api/config', app.views.config),
    path(settings.URL_PREFIX + 'api/report_offline', app.views.report_task),
    path(settings.URL_PREFIX + 'api/finish_task', app.views.private_finish_task),
    path(settings.URL_PREFIX + 'api/pop_queue', app.views.private_pop_queue),
]
