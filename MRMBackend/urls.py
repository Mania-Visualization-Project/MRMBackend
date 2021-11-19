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
import app.views

urlpatterns = [
    path('mania/admin/', admin.site.urls),
    path('mania/api/upload', app.views.upload),
    path('mania/api/generate', app.views.generate),
    path('mania/api/query', app.views.query),
    path('mania/api/download', app.views.download),
    path('mania/api/finish_task', app.views.private_finish_task),
    path('mania/api/pop_queue', app.views.private_pop_queue),
]
