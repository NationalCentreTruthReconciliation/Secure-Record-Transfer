import os
import json

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.crypto import get_random_string
from django.utils import timezone

from recordtransfer.settings import BAG_STORAGE_FOLDER
from recordtransfer.storage import OverwriteStorage


class User(AbstractUser):
    ''' The main User object used to authenticate users. '''
    gets_bag_email_updates = models.BooleanField(default=False)
    confirmed_email = models.BooleanField(default=False)

    def get_full_name(self):
        return self.first_name + ' ' + self.last_name


class UploadSession(models.Model):
    ''' Represents a file upload session, that may or may not be split into multiple parallel
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


class BagGroup(models.Model):
    name = models.CharField(max_length=256, null=False)
    description = models.TextField(default='')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f'{self.name} (Created by {self.created_by})'


class Bag(models.Model):
    ''' A bag that a user submitted. '''
    class ReviewStatus(models.TextChoices):
        ''' The status of the bag's review '''
        NOT_REVIEWED = 'NR', _('Not Reviewed')
        REVIEW_STARTED = 'RS', _('Review Started')
        REVIEW_COMPLETE = 'RC', _('Review Complete')

    bagging_date = models.DateTimeField()
    part_of_group = models.ForeignKey(BagGroup, on_delete=models.SET_NULL, null=True)
    bag_name = models.CharField(max_length=256, null=True)
    caais_metadata = models.TextField(default=r'{}')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    review_status = models.CharField(max_length=2, choices=ReviewStatus.choices,
                                     default=ReviewStatus.NOT_REVIEWED)

    @property
    def location(self):
        return os.path.join(BAG_STORAGE_FOLDER, self.user.username, self.bag_name)

    @property
    def transfer_info(self):
        ''' Exposes a small amount of information from the transfer to be shown for a user '''
        json_metadata = json.loads(self.caais_metadata)
        title = json_metadata['section_1']['accession_title']
        extent = json_metadata['section_3']['extent_statement'][0]['quantity_and_type_of_units']
        return {
            'title': title,
            'extent': extent,
        }

    def get_admin_change_url(self):
        view_name = 'admin:{0}_{1}_change'.format(self._meta.app_label, self._meta.model_name)
        return reverse(view_name, args=(self.pk,))

    def __str__(self):
        return f'{self.bag_name} (Created by {self.user})'


class Job(models.Model):
    ''' A background job executed by an admin user '''
    class JobStatus(models.TextChoices):
        ''' The status of the bag's review '''
        NOT_STARTED = 'NS', _('Not Started')
        IN_PROGRESS = 'IP', _('In Progress')
        COMPLETE = 'CP', _('Complete')
        FAILED = 'FD', _('Failed')

    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True)
    name = models.CharField(max_length=256, null=True)
    description = models.TextField(null=True)
    user_triggered = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    job_status = models.CharField(max_length=2, choices=JobStatus.choices,
                                  default=JobStatus.NOT_STARTED)
    attached_file = models.FileField(upload_to='jobs/zipped_bags', storage=OverwriteStorage,
                                     blank=True, null=True)

    def __str__(self):
        return f'{self.name} (Created by {self.user_triggered})'
