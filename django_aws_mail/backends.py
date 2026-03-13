"""
Mail backend for handling AWS SES via boto3.
Inspired by django-amazon-ses.
"""
import boto3
from botocore.exceptions import ClientError, BotoCoreError

from django.core.mail.backends.base import BaseEmailBackend
from django_aws_mail.signals import mail_pre_send, mail_post_send
from django_aws_mail.config import mail_settings


class EmailBackend(BaseEmailBackend):
    """
    An email backend for use with Amazon SESv2.
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sesv2.html

    Overrides the default setting:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.region_name = kwargs.get('aws_region_name') or mail_settings.AWS_REGION_NAME
        self.access_key_id = kwargs.get('aws_access_key_id') or mail_settings.AWS_ACCESS_KEY_ID
        self.secret_access_key = kwargs.get('aws_secret_access_key') or mail_settings.AWS_SECRET_ACCESS_KEY
        self.connection = None

    def open(self):
        if self.connection:
            return False
        try:
            self.connection = boto3.client(
                'sesv2',
                region_name=self.region_name,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key
            )
            return True
        except Exception:
            if not self.fail_silently:
                raise
            return False

    def close(self):
        if self.connection:
            self.connection = None

    def _prepare_message(self, email_message):
        """Extracts envelope info and generates raw MIME data."""
        from email.utils import parseaddr
        from django import get_version

        # clean recipients for the routing envelope
        recipients = [parseaddr(addr)[1] for addr in email_message.recipients()]

        if get_version() < '6.0':
            # Support for legacy Django MIME handling
            data = email_message.message().as_bytes(linesep='\r\n')
        else:
            import email.policy
            # use the standard SMTP policy to ensure strict 7-bit ASCII encoding
            data = email_message.message(policy=email.policy.SMTP).as_bytes()

        return recipients, data

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        self.open()
        if not self.connection:
            return 0

        num_sent = 0
        for msg in email_messages:
            if self._send(msg):
                num_sent += 1

        return num_sent

    def _send(self, email_message):
        mail_pre_send.send(self.__class__, message=email_message)
        if not email_message.recipients():
            return False

        recipients, data = self._prepare_message(email_message)

        try:
            response = self.connection.send_email(
                Destination={'ToAddresses': recipients},
                Content={'Raw': {'Data': data}}
            )
        except (BotoCoreError, ClientError):
            if not self.fail_silently:
                raise
            return False

        mail_post_send.send(self.__class__, message=email_message, response=response)
        return True
