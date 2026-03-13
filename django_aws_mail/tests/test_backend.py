from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError

from django.test import TestCase
from django.core.mail import EmailMessage

from django_aws_mail.backends import EmailBackend
from django_aws_mail.signals import mail_pre_send, mail_post_send


class EmailBackendTests(TestCase):
    def setUp(self):
        # Set up a backend with dummy credentials for testing
        self.backend = EmailBackend(
            aws_region_name='eu-west-1',
            aws_access_key_id='test-key',
            aws_secret_access_key='test-secret',
            fail_silently=False
        )
        self.email = EmailMessage(
            subject='Test Subject',
            body='Test Body',
            from_email='"Test Sender" <sender@example.com>',
            to=['"Recipient 1" <rec1@example.com>', 'rec2@example.com']
        )

    @patch('django_aws_mail.backends.boto3.client')
    def test_open_connection(self, mock_boto_client):
        """Test that the Boto3 client is initialized with correct credentials."""
        self.backend.open()

        mock_boto_client.assert_called_once_with(
            'sesv2',
            region_name='eu-west-1',
            aws_access_key_id='test-key',
            aws_secret_access_key='test-secret'
        )
        self.assertIsNotNone(self.backend.connection)

    @patch('django_aws_mail.backends.boto3.client')
    def test_open_connection_fail_silently(self, mock_boto_client):
        """Test that exceptions during connection are caught if fail_silently is True."""
        mock_boto_client.side_effect = Exception("Connection Failed")

        # Should raise if fail_silently is False
        with self.assertRaises(Exception):
            self.backend.open()

        # Should return False if fail_silently is True
        self.backend.fail_silently = True
        self.assertFalse(self.backend.open())

    def test_prepare_message(self):
        """Test that recipients are cleaned and data is generated as bytes."""
        recipients, data = self.backend._prepare_message(self.email)

        # AWS Envelope should only have clean emails, no names
        self.assertEqual(recipients, ['rec1@example.com', 'rec2@example.com'])

        # Data should be raw bytes
        self.assertIsInstance(data, bytes)

        # The raw bytes should contain the formatted From header (with the name)
        self.assertIn(b'From: "Test Sender" <sender@example.com>', data)

    @patch('django_aws_mail.backends.boto3.client')
    def test_send_messages(self, mock_boto_client):
        """Test that send_email is called with the correct AWS payload structure."""
        # Setup the mock connection and its send_email response
        mock_connection = MagicMock()
        mock_connection.send_email.return_value = {'MessageId': '12345'}
        mock_boto_client.return_value = mock_connection

        num_sent = self.backend.send_messages([self.email])

        self.assertEqual(num_sent, 1)

        # Verify the exact payload sent to AWS SES
        call_kwargs = mock_connection.send_email.call_args[1]
        self.assertIn('Destination', call_kwargs)
        self.assertIn('Content', call_kwargs)

        # Destination should only contain clean emails
        self.assertEqual(call_kwargs['Destination']['ToAddresses'],
                         ['rec1@example.com', 'rec2@example.com'])

        # Content should contain the raw MIME bytes
        self.assertIn('Raw', call_kwargs['Content'])
        self.assertIsInstance(call_kwargs['Content']['Raw']['Data'], bytes)

    @patch('django_aws_mail.backends.boto3.client')
    def test_send_messages_client_error(self, mock_boto_client):
        """Test that AWS API errors are handled based on fail_silently."""
        mock_connection = MagicMock()
        # Simulate an AWS ClientError (e.g., identity not verified)
        mock_connection.send_email.side_effect = ClientError(
            {'Error': {'Code': 'MessageRejected', 'Message': 'Email rejected'}},
            'SendEmail'
        )
        mock_boto_client.return_value = mock_connection

        # Should raise by default
        with self.assertRaises(ClientError):
            self.backend.send_messages([self.email])

        # Should return 0 sent messages if fail_silently is True
        self.backend.fail_silently = True
        num_sent = self.backend.send_messages([self.email])
        self.assertEqual(num_sent, 0)

    @patch('django_aws_mail.backends.boto3.client')
    def test_signals_are_sent(self, mock_boto_client):
        """Test that pre and post send signals are dispatched."""
        mock_connection = MagicMock()
        mock_connection.send_email.return_value = {'MessageId': 'mocked-id'}
        mock_boto_client.return_value = mock_connection

        # Set up mock receivers for the signals
        pre_send_receiver = MagicMock()
        post_send_receiver = MagicMock()

        mail_pre_send.connect(pre_send_receiver)
        mail_post_send.connect(post_send_receiver)

        self.backend.send_messages([self.email])

        # Verify pre_send was called with the message
        pre_send_receiver.assert_called_once()
        self.assertEqual(pre_send_receiver.call_args[1]['message'], self.email)

        # Verify post_send was called with the message and the AWS response
        post_send_receiver.assert_called_once()
        self.assertEqual(post_send_receiver.call_args[1]['message'], self.email)
        self.assertEqual(post_send_receiver.call_args[1]['response'], {'MessageId': 'mocked-id'})

        # Disconnect to not pollute other tests
        mail_pre_send.disconnect(pre_send_receiver)
        mail_post_send.disconnect(post_send_receiver)
