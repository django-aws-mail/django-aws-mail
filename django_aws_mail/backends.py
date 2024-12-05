"""
Mail backend for handling AWS SES via boto3.
Inspired by django-amazon-ses.
"""
import boto3
from botocore.exceptions import ClientError, BotoCoreError

from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import sanitize_address

from django_aws_mail.signals import mail_pre_send, mail_post_send
from django_aws_mail import settings


class EmailBackend(BaseEmailBackend):
    """
    An email backend for use with Amazon SESv2.
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sesv2.html

    Overrides the default setting:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    """
    def __init__(self,
                 aws_region_name=None,
                 aws_access_key_id=None,
                 aws_secret_access_key=None,
                 fail_silently=False,
                 **kwargs):

        super().__init__(fail_silently=fail_silently, **kwargs)

        self.region_name = aws_region_name or settings.AWS_REGION_NAME
        self.access_key_id = aws_access_key_id or settings.AWS_ACCESS_KEY_ID
        self.secret_access_key = aws_secret_access_key or settings.AWS_SECRET_ACCESS_KEY

        self.connection = None

    def open(self):
        if self.connection:
            return False

        try:
            self.connection = boto3.client('sesv2',
                                           region_name=self.region_name,
                                           aws_access_key_id=self.access_key_id,
                                           aws_secret_access_key=self.secret_access_key)
        except Exception:
            if not self.fail_silently:
                raise

    def close(self):
        self.connection.close()
        self.connection = None

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        new_conn_created = self.open()
        if not self.connection:
            # fail silently
            return 0

        num_sent = 0
        for message in email_messages:
            sent = self._send(message)
            if sent:
                num_sent += 1

        if new_conn_created:
            self.close()
        return num_sent

    def _send(self, email_message):
        # sending the pre-send signal here allows for changing the message,
        # eg: when removing all recipients (blacklisted) the message will not be sent.
        mail_pre_send.send(self.__class__, message=email_message)

        if not email_message.recipients():
            return False

        encoding = email_message.encoding or settings.DEFAULT_CHARSET
        from_email = sanitize_address(email_message.from_email, encoding)
        recipients = [sanitize_address(addr, encoding) for addr in email_message.recipients()]
        message = email_message.message()

        mail_kwargs = {
            'FromEmailAddress': from_email,
            'Destination': {
                'ToAddresses': recipients,
            },
            'Content': {
                'Raw': {
                    'Data': message.as_bytes(linesep='\r\n'),
                },
            },
        }

        try:
            response = self.connection.send_email(**mail_kwargs)
        except (BotoCoreError, ClientError):
            if not self.fail_silently:
                raise
            return False

        else:
            mail_post_send.send(self.__class__, message=email_message, response=response)

        return True
