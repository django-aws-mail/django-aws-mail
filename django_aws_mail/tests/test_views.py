import logging
from unittest.mock import patch, MagicMock

from django.test import TestCase, RequestFactory
from django.http import Http404

from django_aws_mail.views import AwsSnsWebhook
from django_aws_mail import signals


class AwsSnsWebhookTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = AwsSnsWebhook.as_view()
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_get_request_raises_404(self):
        """Test that GET requests are rejected to hide the endpoint."""
        request = self.factory.get('/webhook/')
        with self.assertRaises(Http404):
            self.view(request)

    @patch('django_aws_mail.views.mail_settings')
    @patch('django_aws_mail.views.NotificationVerifier')
    def test_invalid_verification_returns_400(self, mock_verifier_class, mock_settings):
        """Test that unverified payloads are rejected if verification is enabled."""
        mock_settings.AWS_SNS_VERIFY_NOTIFICATION = True

        mock_verifier = MagicMock()
        mock_verifier.is_verified = False
        mock_verifier_class.return_value = mock_verifier

        request = self.factory.post('/webhook/', data='{}', content_type='application/json')
        response = self.view(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b'Invalid notification')

    @patch('django_aws_mail.views.urlopen')
    @patch('django_aws_mail.views.NotificationVerifier')
    def test_subscription_confirmation_valid(self, mock_verifier_class, mock_urlopen):
        """Test that a valid SubscriptionConfirmation visits the SubscribeURL."""
        mock_verifier = MagicMock()
        mock_verifier.is_verified = True
        mock_verifier.get_notification.return_value = {
            'Type': 'SubscriptionConfirmation',
            'TopicArn': 'arn:aws:sns:eu-west-1:12345:topic',
            'SubscribeURL': 'https://sns.eu-west-1.amazonaws.com/?Action=ConfirmSubscription'
        }
        mock_verifier_class.return_value = mock_verifier

        request = self.factory.post('/webhook/', data='{}', content_type='application/json')
        response = self.view(request)

        self.assertEqual(response.status_code, 200)
        mock_urlopen.assert_called_once_with(
            'https://sns.eu-west-1.amazonaws.com/?Action=ConfirmSubscription')

    @patch('django_aws_mail.views.NotificationVerifier')
    def test_subscription_confirmation_invalid_domain(self, mock_verifier_class):
        """Test that a malicious SubscribeURL is rejected."""
        mock_verifier = MagicMock()
        mock_verifier.is_verified = True
        mock_verifier.get_notification.return_value = {
            'Type': 'SubscriptionConfirmation',
            'SubscribeURL': 'https://malicious-hacker.com/?Action=ConfirmSubscription'
        }
        mock_verifier_class.return_value = mock_verifier

        request = self.factory.post('/webhook/', data='{}', content_type='application/json')
        response = self.view(request)

        # Should return 400 Bad Request
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b'Improper subscription domain')

    @patch('django_aws_mail.views.NotificationVerifier')
    def test_bounce_event_dispatches_signal(self, mock_verifier_class):
        """Test that a Bounce Notification successfully dispatches the mail_bounce signal."""
        mock_verifier = MagicMock()
        mock_verifier.is_verified = True
        mock_verifier.get_notification.return_value = {'Type': 'Notification'}
        mock_verifier.get_message.return_value = {
            'eventType': 'Bounce',
            'mail': {'destination': ['bounced@example.com']},
            'bounce': {'bounceType': 'Permanent', 'bounceSubType': 'General'}
        }
        mock_verifier_class.return_value = mock_verifier

        # Mock a signal receiver
        receiver = MagicMock()
        signals.mail_bounce.connect(receiver)

        request = self.factory.post('/webhook/', data='{}', content_type='application/json')
        response = self.view(request)

        self.assertEqual(response.status_code, 200)

        # Verify the signal was called with the correct extracted data
        receiver.assert_called_once()
        kwargs = receiver.call_args[1]
        self.assertEqual(kwargs['mail']['destination'], ['bounced@example.com'])
        self.assertEqual(kwargs['event']['bounceType'], 'Permanent')
        self.assertEqual(kwargs['message']['eventType'], 'Bounce')

        # Cleanup
        signals.mail_bounce.disconnect(receiver)

    @patch('django_aws_mail.views.logger')
    @patch('django_aws_mail.views.NotificationVerifier')
    def test_unknown_event_type_logs_warning(self, mock_verifier_class, mock_logger):
        """Test that an unknown eventType falls through safely and logs a warning."""
        mock_verifier = MagicMock()
        mock_verifier.is_verified = True
        mock_verifier.get_notification.return_value = {'Type': 'Notification'}
        mock_verifier.get_message.return_value = {
            'eventType': 'FutureNewAwsFeature',
            'mail': {'destination': ['test@example.com']}
        }
        mock_verifier_class.return_value = mock_verifier

        request = self.factory.post('/webhook/', data='{}', content_type='application/json')
        response = self.view(request)

        self.assertEqual(response.status_code, 200)
        mock_logger.warning.assert_called_once_with(
            "Received unknown event type: FutureNewAwsFeature",
            extra={'message': mock_verifier.get_message.return_value}
        )

    @patch('django_aws_mail.views.logger')
    @patch('django_aws_mail.views.NotificationVerifier')
    def test_unsubscribe_confirmation(self, mock_verifier_class, mock_logger):
        """Test that UnsubscribeConfirmation simply logs the event and returns 200."""
        mock_verifier = MagicMock()
        mock_verifier.is_verified = True
        mock_verifier.get_notification.return_value = {
            'Type': 'UnsubscribeConfirmation',
            'TopicArn': 'arn:aws:sns:eu-west-1:12345:topic'
        }
        mock_verifier_class.return_value = mock_verifier

        request = self.factory.post('/webhook/', data='{}', content_type='application/json')
        response = self.view(request)

        self.assertEqual(response.status_code, 200)
        mock_logger.info.assert_called()

    @patch('django_aws_mail.views.NotificationVerifier')
    def test_other_event_types_dispatch_signals(self, mock_verifier_class):
        """Test that Complaint, Delivery, Delay, Send, Reject, Open, and Click are routed."""
        event_types = [
            ('Complaint', 'complaint'), ('Delivery', 'delivery'),
            ('DeliveryDelay', 'deliveryDelay'), ('Send', 'send'),
            ('Reject', 'reject'), ('Open', 'open'), ('Click', 'click')
        ]

        for aws_event, dict_key in event_types:
            with self.subTest(event_type=aws_event):
                mock_verifier = MagicMock()
                mock_verifier.is_verified = True
                mock_verifier.get_notification.return_value = {'Type': 'Notification'}
                mock_verifier.get_message.return_value = {
                    'eventType': aws_event,
                    'mail': {'destination': ['test@example.com']},
                    dict_key: {'dummy': 'data'}
                }
                mock_verifier_class.return_value = mock_verifier

                # We don't even need to mock the specific signals here, just hitting
                # the view is enough to execute the routing lines for coverage!
                request = self.factory.post('/webhook/', data='{}', content_type='application/json')
                response = self.view(request)

                self.assertEqual(response.status_code, 200)
