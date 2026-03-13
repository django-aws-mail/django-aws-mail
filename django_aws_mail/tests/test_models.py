from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError

from django_aws_mail.models import Delay, Bounce, Complaint

User = get_user_model()


@override_settings(MAIL_AWS_TYPES={'newsletter': 'weekly newsletter'})
class ModelTests(TestCase):
    def setUp(self):
        # create a dummy user for foreign key relations
        self.user = User.objects.create_user(username='testuser', password='password')

        # standard dummy mail payload matching AWS SNS structure
        self.dummy_mail = {
            'destination': ['test@example.com'],
            'tags': {'mail-type': ['newsletter']}
        }

    # --- BOUNCE TESTS ---

    def test_bounce_creation_and_str(self):
        """Test basic creation and string representation of a Bounce object."""
        bounce_payload = {
            'bounceType': 'Permanent',
            'bounceSubType': 'General',
            'bouncedRecipients': [{'emailAddress': 'test@example.com'}]
        }

        bounce = Bounce.objects.create(
            user=self.user,
            destination='test@example.com',
            bounce_type='Permanent',
            bounce_sub_type='General',
            bounce=bounce_payload,
            mail=self.dummy_mail
        )

        self.assertEqual(str(bounce), "Permanent Mail Bounce for test@example.com (1)")

    def test_bounce_unique_constraint(self):
        """Test that the unique_bounce constraint prevents exact duplicates."""
        Bounce.objects.create(
            destination='test@example.com', bounce_type='Permanent', bounce_sub_type='General',
            bounce={}, mail={}
        )

        with self.assertRaises(IntegrityError):
            Bounce.objects.create(
                destination='test@example.com', bounce_type='Permanent', bounce_sub_type='General',
                bounce={}, mail={}
            )

    def test_bounce_get_message_known(self):
        """Test humanized message for a known bounce sub-type."""
        bounce_payload = {
            'bounceSubType': 'NoEmail',
            'bouncedRecipients': [{'emailAddress': 'test@example.com'}]
        }
        bounce = Bounce(bounce=bounce_payload, mail=self.dummy_mail)

        msg = bounce.get_message()
        self.assertIn("does not appear to exist", msg)
        self.assertIn("newsletter", msg)  # From get_mail_type
        self.assertIn("test@example.com", msg)

    def test_bounce_get_message_unknown(self):
        """Test humanized message fallback for an unknown bounce sub-type."""
        bounce_payload = {
            'bounceSubType': 'FutureAWSCode',
            'bouncedRecipients': [{'emailAddress': 'test@example.com'}]
        }
        bounce = Bounce(bounce=bounce_payload, mail=self.dummy_mail)

        msg = bounce.get_message()
        self.assertIn("bounced for undetermined reasons", msg)

    def test_bounce_get_message_with_smtp_code(self):
        """Test that SMTP status codes append specific diagnostic explanations."""
        bounce_payload = {
            'bounceSubType': 'General',
            'bouncedRecipients': [{'emailAddress': 'test@example.com', 'status': '5.1.1'}]
        }
        bounce = Bounce(bounce=bounce_payload, mail=self.dummy_mail)

        msg = bounce.get_message()
        self.assertIn("Additionally reported status code 5.1.1:", msg)
        self.assertIn("Probably a typo in the email address before the @.", msg)

    def test_bounce_get_diagnostics(self):
        """Test that diagnostic codes are extracted and urlized."""
        bounce_payload = {
            'bouncedRecipients': [{
                'emailAddress': 'test@example.com',
                'diagnosticCode': 'smtp; 550 5.1.1 User unknown http://help.example.com'
            }]
        }
        bounce = Bounce(bounce=bounce_payload, mail=self.dummy_mail)

        diag = bounce.get_diagnostics()
        self.assertIn('<a href="http://help.example.com">http://help.example.com</a>', diag)

    def test_bounce_get_diagnostics_none(self):
        """Test diagnostic extraction safely returns None if missing."""
        bounce = Bounce(bounce={'bouncedRecipients': [{}]}, mail=self.dummy_mail)
        self.assertIsNone(bounce.get_diagnostics())

    # --- DELAY TESTS ---

    def test_delay_creation_and_str(self):
        """Test basic creation and string representation of a Delay object."""
        delay_payload = {
            'delayType': 'TransientCommunicationFailure',
            'delayedRecipients': [{'emailAddress': 'test@example.com'}]
        }

        delay = Delay.objects.create(
            user=self.user,
            destination='test@example.com',
            delay_type='TransientCommunicationFailure',
            delay=delay_payload,
            mail=self.dummy_mail
        )

        self.assertEqual(str(delay), "Mail Delay for test@example.com (1)")

    def test_delay_unique_constraint(self):
        """Test that the unique_delay constraint prevents exact duplicates."""
        Delay.objects.create(destination='test@example.com', delay_type='IPFailure', delay={},
                             mail={})

        with self.assertRaises(IntegrityError):
            Delay.objects.create(destination='test@example.com', delay_type='IPFailure', delay={},
                                 mail={})

    def test_delay_get_message_known(self):
        """Test humanized message for a known delay type."""
        delay_payload = {'delayType': 'MailboxFull'}
        delay = Delay(delay=delay_payload, mail=self.dummy_mail)

        msg = delay.get_message()
        self.assertIn("mailbox appears to be full", msg)

    def test_delay_get_message_with_smtp_code(self):
        """Test that SMTP status codes append specific diagnostic explanations for delays."""
        delay_payload = {
            'delayType': 'General',
            'delayedRecipients': [{'emailAddress': 'test@example.com', 'status': '4.4.2'}]
        }
        delay = Delay(delay=delay_payload, mail=self.dummy_mail)

        msg = delay.get_message()
        self.assertIn("Additionally reported status code 4.4.2:", msg)
        self.assertIn("Delivery temporarily suspended.", msg)

    def test_delay_get_diagnostics(self):
        """Test that diagnostic codes are extracted for delays."""
        delay_payload = {
            'delayedRecipients': [{'diagnosticCode': '451 Timeout'}]
        }
        delay = Delay(delay=delay_payload, mail=self.dummy_mail)
        self.assertEqual(delay.get_diagnostics(), "<p>451 Timeout</p>")

    def test_delay_get_message_unknown(self):
        """Test humanized message fallback for an unknown delay type."""
        delay_payload = {'delayType': 'SomeFutureDelayType'}
        delay = Delay(delay=delay_payload, mail=self.dummy_mail)

        msg = delay.get_message()
        self.assertIn("delayed for undetermined reasons", msg)

    # --- COMPLAINT TESTS ---

    def test_complaint_creation_and_str(self):
        """Test basic creation and string representation of a Complaint object."""
        complaint_payload = {
            'complainedRecipients': [{'emailAddress': 'test@example.com'}]
        }

        complaint = Complaint.objects.create(
            user=self.user,
            destination='test@example.com',
            complaint_type='abuse',
            complaint=complaint_payload,
            mail=self.dummy_mail
        )

        self.assertEqual(str(complaint), "Mail Complaint for test@example.com (1)")

    def test_complaint_unique_constraint(self):
        """Test that the unique_complaint constraint prevents exact duplicates."""
        Complaint.objects.create(destination='test@example.com', complaint_type='abuse',
                                 complaint={}, mail={})

        with self.assertRaises(IntegrityError):
            Complaint.objects.create(destination='test@example.com', complaint_type='abuse',
                                     complaint={}, mail={})

    def test_complaint_get_message(self):
        """Test humanized message for a complaint."""
        complaint = Complaint(complaint={}, mail=self.dummy_mail)

        msg = complaint.get_message()
        self.assertIn("bounced with a complaint", msg)
        self.assertIn("newsletter", msg)
