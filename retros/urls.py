from django.urls import path

from retros import views

urlpatterns = [
    path("create/", views.create_retro_view, name="retro_create"),
    path("<uuid:pk>/", views.retro_detail_view, name="retro_detail"),
]
