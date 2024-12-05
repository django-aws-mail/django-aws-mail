"""
Webhook for handling AWS SNS event messages.
Inspired by django-bouncy and django-ses.
"""
import re
import logging
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen

from django.http import HttpResponseBadRequest, HttpResponse, Http404
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from django_aws_mail import settings, signals
from django_aws_mail.verifier import NotificationVerifier

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class AwsSnsWebhook(View):
    http_method_names = ['post']

    def http_method_not_allowed(self, request, *args, **kwargs):
        # hide this endpoint, non-POST requests will return an HTTP 404
        raise Http404

    def post(self, request, *args, **kwargs):
        verifier = NotificationVerifier(request)
        if settings.AWS_SNS_VERIFY_NOTIFICATION and not verifier.is_verified:
            return HttpResponseBadRequest('Invalid notification')

        notification = verifier.get_notification()
        if not notification:
            return HttpResponseBadRequest('Invalid notification')

        notification_type = notification.get('Type')
        if notification_type == 'SubscriptionConfirmation':
            self.handle_subscription_confirmation(notification)

        elif notification_type == 'UnsubscribeConfirmation':
            self.handle_unsubscribe_confirmation(notification)

        elif notification_type == 'Notification':
            message = verifier.get_message()
            if message:
                # handle event types
                event_type = message.get('eventType')
                if event_type == 'Bounce':
                    self.handle_bounce(message)
                elif event_type == 'Complaint':
                    self.handle_complaint(message)
                elif event_type == 'Delivery':
                    self.handle_delivery(message)
                elif event_type == 'DeliveryDelay':
                    self.handle_delivery_delay(message)
                elif event_type == 'Send':
                    self.handle_send(message)
                elif event_type == 'Reject':
                    self.handle_reject(message)
                elif event_type == 'Open':
                    self.handle_open(message)
                elif event_type == 'Click':
                    self.handle_click(message)
                else:
                    self.handle_unknown_event(message)

        else:
            self.handle_unknown_notification(notification)

        return HttpResponse('ok')

    def handle_unknown_notification(self, notification):
        logger.warning(f"Received unknown notification type: {notification.get('Type')}",
                       extra={'notification': notification})

    def handle_unknown_event(self, message):
        logger.warning(f"Received unknown event type: {message.get('eventType')}",
                       extra={'message': message})

    def handle_subscription_confirmation(self, notification):
        logger.info((f"Received subscription confirmation, "
                     f"TopicArn: {notification.get('TopicArn')}"),
                    extra={'notification': notification})

        # check subscribe url
        url = notification.get('SubscribeURL')
        domain = urlparse(url).netloc
        pattern = r"sns.[a-z0-9\-]+.amazonaws.com$"
        if not re.search(pattern, domain):
            logger.error(f'Invalid subscription domain {url}')
            return HttpResponseBadRequest('Improper subscription domain')

        # simply visit url
        try:
            _ = urlopen(url).read()
            logger.info(f'Subscription confirmation request sent, URL: {url}')
        except URLError as e:
            logger.error(f'HTTP error creating subscription {e.reason}',
                         extra={'notification': notification})

    def handle_unsubscribe_confirmation(self, notification):
        # log message, no need to visit any url
        logger.info((f"Received unsubscription confirmation, "
                     f"TopicArn: {notification.get('TopicArn')}"),
                    extra={'notification': notification})

    def handle_bounce(self, message):
        self.handle_event('bounce', signals.mail_bounce, message)

    def handle_complaint(self, message):
        self.handle_event('complaint', signals.mail_complaint, message)

    def handle_delivery(self, message):
        self.handle_event('delivery', signals.mail_delivery, message)

    def handle_delivery_delay(self, message):
        self.handle_event('deliveryDelay', signals.mail_delivery_delay, message)

    def handle_send(self, message):
        self.handle_event('send', signals.mail_send, message)

    def handle_reject(self, message):
        self.handle_event('reject', signals.mail_reject, message)

    def handle_open(self, message):
        self.handle_event('open', signals.mail_open, message)

    def handle_click(self, message):
        self.handle_event('click', signals.mail_click, message)

    def handle_event(self, event_name, signal, message):
        mail = message.get('mail')
        event = message.get(event_name, {})

        logger.info(f"Received email {event_name} event for {mail['destination'][0]}")

        kwargs = {
            'sender': self.__class__,
            'mail': mail,
            'event': event,
            'message': message,
        }
        signal.send(**kwargs)
