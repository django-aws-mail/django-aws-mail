import os
from django.conf import settings

# Django's User model
AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')

# email address to use to sent email from
DEFAULT_FROM_EMAIL = getattr(settings, 'DEFAULT_FROM_EMAIL')

AWS_REGION_NAME = getattr(settings, 'AWS_REGION_NAME', os.getenv('AWS_REGION_NAME', 'eu-west-1'))
AWS_ACCESS_KEY_ID = getattr(settings, 'AWS_ACCESS_KEY_ID', os.getenv('AWS_ACCESS_KEY_ID'))
AWS_SECRET_ACCESS_KEY = getattr(settings, 'AWS_SECRET_ACCESS_KEY', os.getenv('AWS_SECRET_ACCESS_KEY'))

# mapping of verbose email types, used in get_message model methods
AWS_MAIL_TYPES = getattr(settings, 'AWS_MAIL_TYPES', None)

AWS_SNS_VERIFY_NOTIFICATION = getattr(settings, 'AWS_SNS_VERIFY_NOTIFICATION', True)

AWS_SNS_VERIFY_CERTIFICATE = getattr(settings, 'AWS_SNS_VERIFY_CERTIFICATE', True)

AMAZON_SNS_TOPIC_ARN = getattr(settings, 'AMAZON_SNS_TOPIC_ARN', None)

DEFAULT_CHARSET = getattr(settings, 'DEFAULT_CHARSET', 'utf-8')
