import os
from django.conf import settings


# Django's User model
AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')

# Django's default FROM email address
DEFAULT_FROM_EMAIL = getattr(settings, 'DEFAULT_FROM_EMAIL')

# Encoding to use when sanitizing email addresses and adding attachments
DEFAULT_CHARSET = getattr(settings, 'DEFAULT_CHARSET', 'utf-8')


# AWS region and access keys
MAIL_AWS_REGION_NAME = getattr(settings, 'MAIL_AWS_REGION_NAME', os.getenv('MAIL_AWS_REGION_NAME', 'eu-west-1'))
MAIL_AWS_ACCESS_KEY_ID = getattr(settings, 'MAIL_AWS_ACCESS_KEY_ID', os.getenv('MAIL_AWS_ACCESS_KEY_ID'))
MAIL_AWS_SECRET_ACCESS_KEY = getattr(settings, 'MAIL_AWS_SECRET_ACCESS_KEY', os.getenv('MAIL_AWS_SECRET_ACCESS_KEY'))

# Mapping of verbose email types, used in get_message model methods
MAIL_TYPES = getattr(settings, 'MAIL_TYPES', None)

# Set to True (default) to verify incoming SNS notifications
MAIL_AWS_SNS_VERIFY_NOTIFICATION = getattr(settings, 'MAIL_AWS_SNS_VERIFY_NOTIFICATION', True)

# Set to True (default) to verify SNS certificates
MAIL_AWS_SNS_VERIFY_CERTIFICATE = getattr(settings, 'MAIL_AWS_SNS_VERIFY_CERTIFICATE', True)

# SNS Topic Amazon Resource Name
MAIL_AWS_SNS_TOPIC_ARN = getattr(settings, 'MAIL_AWS_SNS_TOPIC_ARN', None)
