import os
from django.conf import settings


class AppSettings:
    def __init__(self, prefix):
        self.prefix = prefix

    def _get_setting(self, name, default=None):
        full_name = f"{self.prefix}_{name}"

        # 1. Check Django settings
        if hasattr(settings, full_name):
            return getattr(settings, full_name)

        # 2. Check Environment Variables
        val = os.getenv(full_name)
        if val is not None:
            # Convert string representations of booleans
            normalized_val = val.lower().strip()
            if normalized_val in ('true', '1', 'yes', 'on'):
                return True
            if normalized_val in ('false', '0', 'no', 'off'):
                return False
            return val

        # 3. Fallback to Default
        return default

    @property
    def AWS_REGION_NAME(self):
        return self._get_setting('REGION_NAME', 'us-east-1')

    @property
    def AWS_ACCESS_KEY_ID(self):
        return self._get_setting('ACCESS_KEY_ID')

    @property
    def AWS_SECRET_ACCESS_KEY(self):
        return self._get_setting('SECRET_ACCESS_KEY')

    @property
    def AWS_SNS_VERIFY_NOTIFICATION(self):
        return self._get_setting('SNS_VERIFY_NOTIFICATION', True)

    @property
    def AWS_SNS_VERIFY_CERTIFICATE(self):
        return self._get_setting('SNS_VERIFY_CERTIFICATE', True)

    @property
    def AWS_SNS_TOPIC_ARN(self):
        return self._get_setting('SNS_TOPIC_ARN', None)

    @property
    def MAIL_TYPES(self):
        return self._get_setting('TYPES', None)

# Instantiate once
mail_settings = AppSettings('MAIL_AWS')
