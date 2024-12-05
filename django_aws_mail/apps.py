from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

__all__ = ['MailConfig']


class MailConfig(AppConfig):
    name = 'django_aws_mail'
    label = 'django_aws_mail'
    verbose_name = _("Django AWS Mail")
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        import django_aws_mail.handlers  # noqa
