from django.urls import path

from .views import get_blob

urlpatterns = [
    path("", get_blob, name='get_blob'),
]