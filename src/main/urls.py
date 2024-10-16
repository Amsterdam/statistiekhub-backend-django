"""statistiek_hub URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from . import auth

# admin styling
admin.site.site_header = "Statistiekhub Admin"
admin.site.site_title = "Statistiekhub Admin Portal"
admin.site.index_title = "Welcome to Statistiekhub Portal"

urlpatterns = static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += [ path('get-blob/<path:blob_name>', include("import_export_job.urls")), ]

urlpatterns +=[
        path("login/", auth.oidc_login),
        path("oidc/", include("mozilla_django_oidc.urls")),
 path("", admin.site.urls),
    ]

