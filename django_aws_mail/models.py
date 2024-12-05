from django.db import models
from django.utils import timezone
from django.utils.html import urlize, linebreaks
from django.utils.translation import gettext_lazy as _

from django_aws_mail import settings
from django_aws_mail.utils import get_mail_type

FEEDBACK_BOUNCE_MESSAGE = {
    'General':
        _('The {mail_type} for <b>{email_address}</b> could not be delivered because '
          'of general issues. See details.'),
    'NoEmail':
        _('The {mail_type} for <b>{email_address}</b> bounced because the provided '
          'email address does not appear to exist.'),
    'Suppressed':
        _('The {mail_type} for <b>{email_address}</b> bounced due to previous sending issues.'),
    'OnAccountSuppressionList':
        _('The {mail_type} for <b>{email_address}</b> bounced due to previous sending issues.'),
    'MailboxFull':
        _('The {mail_type} for <b>{email_address}</b> bounced because your inbox '
          'appears to be full.'),
    'ContentRejected':
        _('The {mail_type} for <b>{email_address}</b> was rejected due to suspected SPAM.'),
}

FEEDBACK_DELAY_MESSAGE = {
    'InternalFailure':
        _('The {mail_type} for <b>{email_address}</b> was delayed due to an internal '
          'failure at the MTA.'),
    'General':
        _('The {mail_type} for <b>{email_address}</b> was delayed because there was a '
          'failure of generic nature.'),
    'MailboxFull':
        _('The {mail_type} for <b>{email_address}</b> was delayed because your mailbox '
          'appears to be full and unable to receive additional messages. Make some space!'),
    'SpamDetected':
        _('The {mail_type} for <b>{email_address}</b> was delayed because your mail provider '
          'considers our email to be SPAM.'),
    'RecipientServerError':
        _('The {mail_type} for <b>{email_address}</b> was delayed because there seems '
          'to be a temporary issue at your mail provider.'),
    'IPFailure':
        _('The {mail_type} for <b>{email_address}</b> was delayed because your mail provider '
          'is blocking or throttling mail from our MTA.'),
    'TransientCommunicationFailure':
        _('The {mail_type} for <b>{email_address}</b> was delayed because there was a temporary '
          'communications failure with your mail provider.'),
    'TransientCommunicationGeneral':
        _('The {mail_type} for <b>{email_address}</b> was delayed because there was a temporary '
          'communications failure with your mail provider.'),
}

# https://www.iana.org/assignments/smtp-enhanced-status-codes/smtp-enhanced-status-codes.xhtml
SMTP_STATUS_CODES = {
    '4.4.2': _('Delivery temporarily suspended.'),
    '4.4.7': _('Message expired, mailbox full.'),
    '5.1.0': _('Sender rejected.'),
    '5.1.1': _('Email account does not exist. Probably a typo in the email address before the @.'),
    '5.1.2': _('Unknown mail server.'),
    '5.2.0': _('Mail rejected.'),
    '5.2.1': _('Addressee unknown.'),
    '5.2.2': _('Mailbox full.'),
    '5.3.0': _('Recipient does not exist, invalid mailbox, unknown user.'),
    '5.4.4': _('Invalid domain. Probably a typo in the email address after the @.'),
    '5.5.0': _('Mailbox unavailable.'),
    '5.7.1': _('Message blocked due to spam.'),
}


class Delay(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        related_name='email_delays')

    destination = models.EmailField()

    delay_type = models.CharField(max_length=50, blank=True, null=True)

    delay = models.JSONField()
    mail = models.JSONField()

    updated = models.DateTimeField(_('Date updated'), auto_now=True)
    created = models.DateTimeField(_('Date created'), default=timezone.now)

    count = models.IntegerField(default=1)

    class Meta:
        ordering = ('-created',)
        constraints = [
            models.UniqueConstraint(fields=['destination', 'delay_type'],
                                    name='unique_delay'),
        ]

    def __str__(self):
        return (f"Mail Delay for "
                f"{self.delay['delayedRecipients'][0]['emailAddress']} ({self.count})")

    def get_message(self):
        delay_type = self.delay['delayType']
        if delay_type in FEEDBACK_DELAY_MESSAGE:
            message = FEEDBACK_DELAY_MESSAGE[delay_type]
        else:
            message = 'The {mail_type} was delayed for undetermined reasons.'

        # add mail type and email address to message
        message = message.format(
            mail_type=get_mail_type(self.mail),
            email_address=self.mail['destination'][0])

        status_code = None
        status_message = None
        if 'delayedRecipients' in self.delay and 'status' in self.delay['delayedRecipients'][0]:
            status_code = self.delay['delayedRecipients'][0]['status']
            if status_code in SMTP_STATUS_CODES:
                status_message = SMTP_STATUS_CODES[status_code]

        if status_code and status_message:
            message = (f'{message} Additionally reported status code '
                       f'{status_code}: {status_message}')

        return message

    def get_diagnostics(self):
        diagnostic_message = None
        if ('delayedRecipients' in self.delay and
                'diagnosticCode' in self.delay['delayedRecipients'][0]):
            diagnostic_code = self.delay['delayedRecipients'][0]['diagnosticCode']
            diagnostic_message = urlize(linebreaks(diagnostic_code.strip()))
        return diagnostic_message


class Bounce(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        related_name='email_bounces')

    destination = models.EmailField()

    bounce_type = models.CharField(max_length=50, blank=True, null=True)
    bounce_sub_type = models.CharField(max_length=50, blank=True, null=True)

    bounce = models.JSONField()
    mail = models.JSONField()

    updated = models.DateTimeField(_('Date updated'), auto_now=True)
    created = models.DateTimeField(_('Date created'), default=timezone.now)

    count = models.IntegerField(default=1)

    class Meta:
        ordering = ('-created',)
        constraints = [
            models.UniqueConstraint(fields=['destination', 'bounce_type', 'bounce_sub_type'],
                                    name='unique_bounce'),
        ]

    def __str__(self):
        return (f"{self.bounce_type} Mail Bounce for "
                f"{self.bounce['bouncedRecipients'][0]['emailAddress']} ({self.count})")

    def get_message(self):
        bounce_sub_type = self.bounce['bounceSubType']
        if bounce_sub_type in FEEDBACK_BOUNCE_MESSAGE:
            message = FEEDBACK_BOUNCE_MESSAGE[bounce_sub_type]
        else:
            message = 'The {mail_type} bounced for undetermined reasons.'

        # add mail type and email address to message
        message = message.format(
            mail_type=get_mail_type(self.mail),
            email_address=self.mail['destination'][0])

        status_code = None
        status_message = None
        if 'bouncedRecipients' in self.bounce and 'status' in self.bounce['bouncedRecipients'][0]:
            status_code = self.bounce['bouncedRecipients'][0]['status']
            if status_code in SMTP_STATUS_CODES:
                status_message = SMTP_STATUS_CODES[status_code]

        if status_code and status_message:
            message = (f'{message} Additionally reported status code '
                       f'{status_code}: {status_message}')

        return message

    def get_diagnostics(self):
        diagnostic_message = None
        if ('bouncedRecipients' in self.bounce and
                'diagnosticCode' in self.bounce['bouncedRecipients'][0]):
            diagnostic_code = self.bounce['bouncedRecipients'][0]['diagnosticCode']
            diagnostic_message = urlize(linebreaks(diagnostic_code.strip()))

        return diagnostic_message


class Complaint(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        related_name='email_complaints')

    destination = models.EmailField()

    complaint_type = models.CharField(max_length=50, blank=True, null=True)

    complaint = models.JSONField()
    mail = models.JSONField()

    updated = models.DateTimeField(_('Date updated'), auto_now=True)
    created = models.DateTimeField(_('Date created'), default=timezone.now)

    count = models.IntegerField(default=1)

    class Meta:
        ordering = ('-created',)
        constraints = [
            models.UniqueConstraint(fields=['destination', 'complaint_type'],
                                    name='unique_complaint'),
        ]

    def __str__(self):
        return (f"Mail Complaint for "
                f"{self.complaint['complainedRecipients'][0]['emailAddress']} ({self.count})")

    def get_message(self):
        message = (
            'The {mail_type} for <b>{email_address}</b> could not be delivered because it '
            'bounced with a complaint, probably due to SPAM rules at your mail provider.')

        # add mail type and email address to message
        message = message.format(
            mail_type=get_mail_type(self.mail),
            email_address=self.mail['destination'][0])

        return message
