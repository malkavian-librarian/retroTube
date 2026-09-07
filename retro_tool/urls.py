"""
URL configuration for retro_tool project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""

from django.contrib import admin
from django.http import HttpResponse
from django.urls import path


def healthcheck(request):
    # Scaffolding-only placeholder — replaced by the real Create/Join flow
    # once retros app views land (see _docs/tasks.md, Task 3).
    return HttpResponse("OK")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", healthcheck, name="healthcheck"),
]
