import json
import logging
from unittest.mock import patch, MagicMock

from django.test import TestCase, RequestFactory

from django_aws_mail.verifier import NotificationVerifier


class NotificationVerifierTests(TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)

        self.factory = RequestFactory()

        # A valid baseline SNS notification payload
        self.valid_payload = {
            "Type": "Notification",
            "MessageId": "12345",
            "TopicArn": "arn:aws:sns:eu-west-1:123:topic",
            "Message": '{"eventType": "Bounce"}',
            "Timestamp": "2026-03-12T12:00:00.000Z",
            "SignatureVersion": "1",
            "Signature": "base64mock==",
            "SigningCertURL": "https://sns.eu-west-1.amazonaws.com/SimpleNotificationService-mock.pem"
        }

        self.valid_request = self.factory.post(
            '/webhook/',
            data=json.dumps(self.valid_payload),
            content_type='application/json',
            HTTP_X_AMZ_SNS_TOPIC_ARN='arn:aws:sns:eu-west-1:123:topic',
            HTTP_X_AMZ_SNS_MESSAGE_TYPE='Notification'
        )

    def tearDown(self):
        logging.disable(logging.NOTSET)

    @patch('django_aws_mail.verifier.mail_settings')
    def test_check_topic_header_success(self, mock_settings):
        """Test that the topic header matches the settings exactly."""
        mock_settings.AWS_SNS_TOPIC_ARN = ['arn:aws:sns:eu-west-1:123:topic']
        verifier = NotificationVerifier(self.valid_request)
        self.assertTrue(verifier.check_topic_header())

    @patch('django_aws_mail.verifier.mail_settings')
    def test_check_topic_header_missing(self, mock_settings):
        """Test failure when the topic header is completely missing."""
        mock_settings.AWS_SNS_TOPIC_ARN = ['arn:aws:sns:eu-west-1:123:topic']

        # Request missing the HTTP_X_AMZ_SNS_TOPIC_ARN header
        bad_request = self.factory.post('/webhook/', data='{}', content_type='application/json')
        verifier = NotificationVerifier(bad_request)
        self.assertFalse(verifier.check_topic_header())

    def test_check_message_type_header(self):
        """Test that only allowed AWS SNS message types are processed."""
        verifier = NotificationVerifier(self.valid_request)
        self.assertTrue(verifier.check_message_type_header())

        bad_request = self.factory.post(
            '/webhook/', data='{}', content_type='application/json',
            HTTP_X_AMZ_SNS_MESSAGE_TYPE='HackerType'
        )
        bad_verifier = NotificationVerifier(bad_request)
        self.assertFalse(bad_verifier.check_message_type_header())

    def test_check_notification_valid_json(self):
        """Test that the JSON body is successfully parsed and stored."""
        verifier = NotificationVerifier(self.valid_request)
        self.assertTrue(verifier.check_notification())
        self.assertEqual(verifier._notification['MessageId'], '12345')

    def test_check_notification_invalid_json(self):
        """Test that malformed JSON is caught and rejected."""
        bad_request = self.factory.post('/webhook/', data='{badjson',
                                        content_type='application/json')
        verifier = NotificationVerifier(bad_request)
        self.assertFalse(verifier.check_notification())

    def test_check_keys(self):
        """Test that all required AWS fields exist in the payload."""
        verifier = NotificationVerifier(self.valid_request)
        verifier.check_notification()  # Load the payload first
        self.assertTrue(verifier.check_keys())

        # Remove a required key
        del self.valid_payload['Signature']
        bad_request = self.factory.post('/webhook/', data=json.dumps(self.valid_payload),
                                        content_type='application/json')
        bad_verifier = NotificationVerifier(bad_request)
        bad_verifier.check_notification()
        self.assertFalse(bad_verifier.check_keys())

    @patch('django_aws_mail.verifier.mail_settings')
    @patch('django_aws_mail.verifier.x509')
    @patch('django_aws_mail.verifier.NotificationVerifier.get_keyfile')
    def test_check_cert_success(self, mock_get_keyfile, mock_x509, mock_settings):
        """Test the full certificate and signature validation flow."""
        mock_settings.AWS_SNS_VERIFY_CERTIFICATE = True

        # Mock the certificate download and parsing
        mock_get_keyfile.return_value = b'mock-pem-data'
        mock_cert = MagicMock()
        mock_public_key = MagicMock()
        # verify() returning None means the signature is valid in cryptography library
        mock_public_key.verify.return_value = None
        mock_cert.public_key.return_value = mock_public_key
        mock_x509.load_pem_x509_certificate.return_value = mock_cert

        verifier = NotificationVerifier(self.valid_request)
        verifier.check_notification()  # Load payload

        self.assertTrue(verifier.check_cert())
        mock_public_key.verify.assert_called_once()

    @patch('django_aws_mail.verifier.mail_settings')
    @patch('django_aws_mail.verifier.x509')
    @patch('django_aws_mail.verifier.NotificationVerifier.get_keyfile')
    def test_check_cert_invalid_signature(self, mock_get_keyfile, mock_x509, mock_settings):
        """Test that an InvalidSignature exception results in a False return."""
        mock_settings.AWS_SNS_VERIFY_CERTIFICATE = True

        from cryptography.exceptions import InvalidSignature

        mock_get_keyfile.return_value = b'mock-pem-data'
        mock_cert = MagicMock()
        mock_public_key = MagicMock()
        # Simulate a cryptographic mismatch
        mock_public_key.verify.side_effect = InvalidSignature()
        mock_cert.public_key.return_value = mock_public_key
        mock_x509.load_pem_x509_certificate.return_value = mock_cert

        verifier = NotificationVerifier(self.valid_request)
        verifier.check_notification()

        self.assertFalse(verifier.check_cert())

    def test_check_cert_invalid_domain(self):
        """Test that certificates hosted on non-AWS domains are instantly rejected."""
        self.valid_payload['SigningCertURL'] = "https://hacker.com/cert.pem"
        bad_request = self.factory.post('/webhook/', data=json.dumps(self.valid_payload),
                                        content_type='application/json')

        verifier = NotificationVerifier(bad_request)
        verifier.check_notification()

        self.assertFalse(verifier.check_cert())

    def test_get_canonical_message(self):
        """Test that the canonical string is built exactly to AWS specs."""
        verifier = NotificationVerifier(self.valid_request)
        verifier.check_notification()

        canonical = verifier.get_canonical_message()

        # Ensure it's a byte string
        self.assertIsInstance(canonical, bytes)

        # Ensure specific required fields made it into the canonical string
        canonical_str = canonical.decode('utf-8')
        self.assertIn('Message\n{"eventType": "Bounce"}\n', canonical_str)
        self.assertIn('TopicArn\narn:aws:sns:eu-west-1:123:topic\n', canonical_str)

    def test_check_message_valid(self):
        """Test that the internal 'Message' JSON string is parsed successfully."""
        verifier = NotificationVerifier(self.valid_request)
        verifier.check_notification()

        self.assertTrue(verifier.check_message())
        self.assertEqual(verifier._message['eventType'], 'Bounce')

    @patch('django_aws_mail.verifier.cache')
    @patch('django_aws_mail.verifier.requests.get')
    def test_get_keyfile_caching(self, mock_requests_get, mock_cache):
        """Test that certificates are fetched and cached correctly."""
        # 1. Test cache miss (fetches from web)
        mock_cache.get.return_value = None
        mock_response = MagicMock()
        mock_response.content = b'downloaded-cert'
        mock_requests_get.return_value = mock_response

        cert_url = 'https://sns.eu-west-1.amazonaws.com/cert.pem'
        result = NotificationVerifier.get_keyfile(cert_url)

        self.assertEqual(result, b'downloaded-cert')
        mock_requests_get.assert_called_once_with(cert_url)
        mock_cache.set.assert_called_once_with(cert_url, b'downloaded-cert')

        # 2. Test cache hit
        mock_requests_get.reset_mock()
        mock_cache.get.return_value = b'cached-cert'

        result2 = NotificationVerifier.get_keyfile(cert_url)
        self.assertEqual(result2, b'cached-cert')
        mock_requests_get.assert_not_called()  # Should not hit the web!
