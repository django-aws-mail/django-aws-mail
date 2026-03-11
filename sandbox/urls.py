from django.contrib import admin
from django.urls import path, include

app_name = 'sandbox'

urlpatterns = [
    path('mail/', include('django_aws_mail.urls', namespace='mail')),
    path('admin/', admin.site.urls),
]
