from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from django_aws_mail.utils import get_mail_type, admin_change_url, admin_link
from django_aws_mail.models import Bounce

User = get_user_model()


class DummyAdmin:
    """A fake ModelAdmin class to test the decorator."""

    @admin_link('user', 'User Link', empty_description='No User Attached')
    def get_user_link(self, user_obj):
        # The wrapped function just needs to return the link text
        return user_obj.username


@override_settings(MAIL_AWS_TYPES={'newsletter': 'Weekly Newsletter'})
class UtilsTests(TestCase):
    def setUp(self):
        # Set up some database objects to test the URL/admin generation
        self.user = User.objects.create_user(username='admin_test', password='password')

        self.bounce_with_user = Bounce.objects.create(
            user=self.user,
            destination='test@example.com',
            bounce={},
            mail={}
        )

        self.bounce_no_user = Bounce.objects.create(
            user=None,
            destination='nouser@example.com',
            bounce={},
            mail={}
        )

        self.dummy_admin = DummyAdmin()

    # --- get_mail_type TESTS ---

    def test_get_mail_type_valid(self):
        """Test getting a known mail type from the tags dictionary."""
        mail = {'tags': {'mail-type': ['newsletter']}}
        self.assertEqual(get_mail_type(mail), 'Weekly Newsletter')

    def test_get_mail_type_unknown(self):
        """Test fallback when the mail-type value isn't in our settings dictionary."""
        mail = {'tags': {'mail-type': ['future_type']}}
        self.assertEqual(get_mail_type(mail), 'email of unknown type')

    def test_get_mail_type_missing_keys(self):
        """Test graceful fallback when the payload is missing tags entirely."""
        self.assertEqual(get_mail_type({}), 'email of unknown type')
        self.assertEqual(get_mail_type({'tags': {}}), 'email of unknown type')

    # --- admin_change_url TESTS ---

    def test_admin_change_url(self):
        """Test that the correct admin URL is dynamically generated for an object."""
        # This should generate something like '/admin/auth/user/1/change/'
        expected_url = reverse('admin:auth_user_change', args=(self.user.pk,))
        url = admin_change_url(self.user)
        self.assertEqual(url, expected_url)

    # --- admin_link TESTS ---

    def test_admin_link_with_related_object(self):
        """Test that the decorator generates a valid HTML anchor tag."""
        html_output = self.dummy_admin.get_user_link(self.bounce_with_user)

        expected_url = reverse('admin:auth_user_change', args=(self.user.pk,))
        expected_html = f'<a href="{expected_url}">admin_test</a>'

        self.assertEqual(html_output, expected_html)

    def test_admin_link_empty_relation(self):
        """Test that the decorator safely handles None relations."""
        html_output = self.dummy_admin.get_user_link(self.bounce_no_user)
        self.assertEqual(html_output, 'No User Attached')

    def test_admin_link_function_attributes(self):
        """Test that the decorator correctly assigns Django admin configuration attributes."""
        # Django admin needs these to know how to render the column!
        self.assertEqual(DummyAdmin.get_user_link.short_description, 'User Link')
        self.assertTrue(DummyAdmin.get_user_link.allow_tags)
