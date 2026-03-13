from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings
from django.core.mail import EmailMultiAlternatives

from django_aws_mail.message import compose


class ComposeTests(TestCase):

    @patch('django_aws_mail.message.render_to_string')
    @patch('django_aws_mail.message.HTMLParser')
    def test_compose_basic(self, mock_html_parser, mock_render):
        """Test the standard creation of an EmailMultiAlternatives object."""
        # Setup mocks
        mock_render.return_value = "<html><body><p>Hello World</p></body></html>"
        mock_parser_instance = MagicMock()
        mock_parser_instance.text.return_value = "Hello World"
        mock_html_parser.return_value = mock_parser_instance

        # Call compose
        message = compose(
            recipients="customer@example.com",  # Passing string to test conversion
            subject="Welcome!",
            template="dummy_template.html",
            context={"name": "John"},
            from_email="sales@example.com"
        )

        # Verify basic message properties
        self.assertIsInstance(message, EmailMultiAlternatives)
        self.assertEqual(message.to, ["customer@example.com"])
        self.assertEqual(message.subject, "Welcome!")
        self.assertEqual(message.from_email, "sales@example.com")
        self.assertEqual(message.body, "Hello World")

        # Verify HTML alternative was attached
        self.assertEqual(len(message.alternatives), 1)
        self.assertEqual(message.alternatives[0][0],
                         "<html><body><p>Hello World</p></body></html>")
        self.assertEqual(message.alternatives[0][1], "text/html")

        # Verify template rendering was called correctly
        mock_render.assert_called_once_with("dummy_template.html", {"name": "John"})

    @patch('django_aws_mail.message.render_to_string')
    @patch('django_aws_mail.message.HTMLParser')
    def test_subject_sanitization(self, mock_html_parser, mock_render):
        """Test that newlines in the subject are removed to prevent header injection."""
        mock_render.return_value = "<p>Test</p>"

        message = compose(
            recipients=["test@example.com"],
            subject="This has\nTwo Lines\r\nAnd More",
            template="dummy.html"
        )

        self.assertEqual(message.subject, "This hasTwo LinesAnd More")

    @override_settings(DEFAULT_FROM_EMAIL='default@example.com')
    @patch('django_aws_mail.message.render_to_string')
    @patch('django_aws_mail.message.HTMLParser')
    def test_default_from_email(self, mock_html_parser, mock_render):
        """Test fallback to settings.DEFAULT_FROM_EMAIL when from_email is None."""
        mock_render.return_value = "<p>Test</p>"

        message = compose(
            recipients=["test@example.com"],
            subject="Test",
            template="dummy.html",
            from_email=None
        )

        self.assertEqual(message.from_email, "default@example.com")

    @patch('django_aws_mail.message.render_to_string')
    @patch('django_aws_mail.message.HTMLParser')
    def test_from_email_tuple_formatting(self, mock_html_parser, mock_render):
        """Test that a tuple passed to from_email is correctly formatted into a string."""
        mock_render.return_value = "<p>Test</p>"

        message = compose(
            recipients=["test@example.com"],
            subject="Test",
            template="dummy.html",
            from_email=("John Doe", "john@example.com")
        )

        self.assertEqual(message.from_email, "John Doe <john@example.com>")

    @patch('django_aws_mail.message.render_to_string')
    @patch('django_aws_mail.message.HTMLParser')
    def test_ses_custom_headers(self, mock_html_parser, mock_render):
        """Test that config_set and mail_type inject the correct AWS SES headers."""
        mock_render.return_value = "<p>Test</p>"

        message = compose(
            recipients=["test@example.com"],
            subject="Test",
            template="dummy.html",
            headers={"Reply-To": "support@example.com"},
            config_set="my-ses-config",
            mail_type="transactional",
            reply_to=["other@example.com"]  # Testing pass-through kwargs
        )

        # Check standard headers injection
        self.assertEqual(message.extra_headers['Reply-To'], "support@example.com")
        self.assertEqual(message.extra_headers['X-Ses-Configuration-Set'], "my-ses-config")
        self.assertEqual(message.extra_headers['X-Ses-Message-Tags'], "mail-type=transactional")

        # Check pass-through kwargs
        self.assertEqual(message.reply_to, ["other@example.com"])
