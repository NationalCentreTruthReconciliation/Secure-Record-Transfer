from django.test import TestCase

from recordtransfer.forms import UserProfileForm
from recordtransfer.models import User


class UserProfileFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='old_password',
            gets_notification_emails=False
        )

    def test_form_valid_data(self):
        form_data = {
            'gets_notification_emails': True,
            'current_password': 'old_password',
            'new_password': 'new_password123',
            'confirm_new_password': 'new_password123',
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertTrue(user.check_password('new_password123'))

    def test_form_invalid_current_password(self):
        form_data = {
            'current_password': 'wrong_password',
            'new_password': 'new_password123',
            'confirm_new_password': 'new_password123',
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('current_password', form.errors)

    def test_form_passwords_do_not_match(self):
        form_data = {
            'current_password': 'old_password',
            'new_password': 'new_password123',
            'confirm_new_password': 'different_password',
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('confirm_new_password', form.errors)

    def test_form_no_changes(self):
        form_data = {}
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertIn('No fields have been changed.', form.errors['__all__'])

    def test_form_email_notification_initial_false(self):
        form_data = {
            'gets_notification_emails': True,
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertTrue(user.gets_notification_emails)

    def test_form_email_notification_initial_true(self):
        self.user.gets_notification_emails = True
        self.user.save()

        form_data = {
            'gets_notification_emails': False,
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertFalse(user.gets_notification_emails)
