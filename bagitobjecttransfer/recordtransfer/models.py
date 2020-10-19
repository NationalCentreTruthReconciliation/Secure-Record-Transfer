import os

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils.crypto import get_random_string
from django.utils import timezone


class User(AbstractUser):
    ''' The main User object used to authenticate users. '''
    gets_bag_email_updates = models.BooleanField(default=False)


class UploadSession(models.Model):
    ''' Represents a file upload session, that may or may not be split into multiple parallel \
    uploads.
    '''
    token = models.CharField(max_length=32)
    started_at = models.DateTimeField()

    @classmethod
    def new_session(cls):
        ''' Start a new upload session '''
        return cls(token=get_random_string(length=32), started_at=timezone.now())

    def __str__(self):
        return f'{self.token} ({self.started_at})'


class UploadedFile(models.Model):
    ''' Represents a file that a user uploaded during an upload session. '''
    name = models.CharField(max_length=256)
    path = models.CharField(max_length=256)
    old_copy_removed = models.BooleanField()
    session = models.ForeignKey(UploadSession, on_delete=models.CASCADE, null=True)

    def delete_file(self):
        try:
            os.remove(str(self.path))
        except FileNotFoundError:
            pass
        finally:
            self.old_copy_removed = True
            self.save()

    def __str__(self):
        if self.old_copy_removed:
            return f'{self.path}, session {self.session}, DELETED'
        return f'{self.path}, session {self.session}, NOT DELETED'


class Bag(models.Model):
    ''' A bag that a user submitted. '''
    class ReviewStatus(models.TextChoices):
        ''' The status of the bag's review '''
        NOT_REVIEWED = 'NR', _('Not Reviewed')
        REVIEW_STARTED = 'RS', _('Review Started')
        REVIEW_COMPLETE = 'RC', _('Review Complete')

    bagging_date = models.DateTimeField()
    bag_name = models.CharField(max_length=256, null=True)
    caais_metadata = models.TextField(default=r'{}')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    review_status = models.CharField(max_length=2, choices=ReviewStatus.choices,
                                     default=ReviewStatus.NOT_REVIEWED)

    def __str__(self):
        return f"Bag created by {self.user} at {self.bagging_date}"
