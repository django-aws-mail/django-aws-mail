import logging
from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth import get_user_model

from django_aws_mail.models import Delay, Bounce, Complaint
from django_aws_mail.handlers import (
    handle_delivery, handle_delay, handle_bounce, handle_complaint
)

User = get_user_model()


class HandlerTests(TestCase):
    def setUp(self):
        # Mute logging to keep test output clean
        logging.disable(logging.CRITICAL)

        # Create a real user to test the lookup logic
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )

        # Standard payloads
        self.known_mail = {'destination': ['test@example.com']}
        self.unknown_mail = {'destination': ['nobody@example.com']}
        self.message = {'mock': 'data'}

    def tearDown(self):
        logging.disable(logging.NOTSET)

    # --- DELIVERY TESTS ---

    @patch('django_aws_mail.handlers.logger')
    def test_handle_delivery(self, mock_logger):
        """Test that delivery events are safely logged without DB interaction."""
        handle_delivery(sender=None, mail=self.known_mail, event={}, message=self.message)
        mock_logger.debug.assert_called_once()

    # --- DELAY TESTS ---

    def test_handle_delay_creates_with_user(self):
        """Test creating a Delay record linked to an existing user."""
        event = {'delayType': 'MailboxFull'}

        handle_delay(sender=None, mail=self.known_mail, event=event, message=self.message)

        delay = Delay.objects.get(destination='test@example.com')
        self.assertEqual(delay.user, self.user)
        self.assertEqual(delay.delay_type, 'MailboxFull')
        self.assertEqual(delay.count, 1)

    def test_handle_delay_creates_without_user(self):
        """Test creating a Delay record when the user does not exist."""
        event = {'delayType': 'General'}

        handle_delay(sender=None, mail=self.unknown_mail, event=event, message=self.message)

        delay = Delay.objects.get(destination='nobody@example.com')
        self.assertIsNone(delay.user)
        self.assertEqual(delay.count, 1)

    def test_handle_delay_updates_existing(self):
        """Test that a recurring delay updates the payload and increments the count."""
        event = {'delayType': 'General', 'status': 'first'}
        handle_delay(sender=None, mail=self.known_mail, event=event, message=self.message)

        # Send a second delay of the exact same type but with updated JSON data
        updated_event = {'delayType': 'General', 'status': 'second'}
        handle_delay(sender=None, mail=self.known_mail, event=updated_event, message=self.message)

        delay = Delay.objects.get(destination='test@example.com')
        self.assertEqual(delay.count, 2)
        self.assertEqual(delay.delay['status'], 'second')  # Proves obj.delay = event worked

    # --- BOUNCE TESTS ---

    def test_handle_bounce_creates_with_user(self):
        """Test creating a Bounce record linked to an existing user."""
        event = {'bounceType': 'Permanent', 'bounceSubType': 'General'}

        handle_bounce(sender=None, mail=self.known_mail, event=event, message=self.message)

        bounce = Bounce.objects.get(destination='test@example.com')
        self.assertEqual(bounce.user, self.user)
        self.assertEqual(bounce.bounce_type, 'Permanent')
        self.assertEqual(bounce.count, 1)

    def test_handle_bounce_creates_without_user(self):
        """Test creating a Bounce record when the user does not exist."""
        event = {'bounceType': 'Permanent', 'bounceSubType': 'General'}

        handle_bounce(sender=None, mail=self.unknown_mail, event=event, message=self.message)

        bounce = Bounce.objects.get(destination='nobody@example.com')
        self.assertIsNone(bounce.user)

    def test_handle_bounce_updates_existing(self):
        """Test that a recurring bounce updates the payload and increments the count."""
        event = {'bounceType': 'Transient', 'bounceSubType': 'MailboxFull', 'status': 'first'}
        handle_bounce(sender=None, mail=self.known_mail, event=event, message=self.message)

        updated_event = {'bounceType': 'Transient', 'bounceSubType': 'MailboxFull',
                         'status': 'second'}
        handle_bounce(sender=None, mail=self.known_mail, event=updated_event, message=self.message)

        bounce = Bounce.objects.get(destination='test@example.com')
        self.assertEqual(bounce.count, 2)
        self.assertEqual(bounce.bounce['status'], 'second')

    # --- COMPLAINT TESTS ---

    def test_handle_complaint_creates_with_user(self):
        """Test creating a Complaint record linked to an existing user."""
        event = {'complaintSubType': 'abuse'}

        handle_complaint(sender=None, mail=self.known_mail, event=event, message=self.message)

        complaint = Complaint.objects.get(destination='test@example.com')
        self.assertEqual(complaint.user, self.user)
        self.assertEqual(complaint.complaint_type, 'abuse')
        self.assertEqual(complaint.count, 1)

    def test_handle_complaint_creates_without_user(self):
        """Test creating a Complaint record when the user does not exist."""
        event = {'complaintSubType': 'abuse'}

        handle_complaint(sender=None, mail=self.unknown_mail, event=event, message=self.message)

        complaint = Complaint.objects.get(destination='nobody@example.com')
        self.assertIsNone(complaint.user)

    def test_handle_complaint_updates_existing(self):
        """Test that a recurring complaint updates the payload and increments the count."""
        event = {'complaintSubType': 'abuse', 'status': 'first'}
        handle_complaint(sender=None, mail=self.known_mail, event=event, message=self.message)

        updated_event = {'complaintSubType': 'abuse', 'status': 'second'}
        handle_complaint(sender=None, mail=self.known_mail, event=updated_event,
                         message=self.message)

        complaint = Complaint.objects.get(destination='test@example.com')
        self.assertEqual(complaint.count, 2)
        self.assertEqual(complaint.complaint['status'], 'second')
