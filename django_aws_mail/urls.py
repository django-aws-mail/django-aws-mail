from django.urls import path

from django_aws_mail.views import AwsSnsWebhook

app_name = 'django_aws_mail'

urlpatterns = [
    path('track/', AwsSnsWebhook.as_view()),
]
