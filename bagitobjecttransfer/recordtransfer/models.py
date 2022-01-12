''' Record Transfer application models '''
import os
import json
import shutil

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _

from recordtransfer.settings import BAG_STORAGE_FOLDER
from recordtransfer.storage import OverwriteStorage


class User(AbstractUser):
    ''' The main User object used to authenticate users
    '''
    gets_bag_email_updates = models.BooleanField(default=False)
    confirmed_email = models.BooleanField(default=False)

    def get_full_name(self):
        return self.first_name + ' ' + self.last_name


class UploadSession(models.Model):
    ''' Represents a file upload session, that may or may not be split into
    multiple parallel uploads
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
    ''' Represents a file that a user uploaded during an upload session
    '''
    name = models.CharField(max_length=256)
    path = models.CharField(max_length=256)
    old_copy_removed = models.BooleanField()
    session = models.ForeignKey(UploadSession, on_delete=models.CASCADE, null=True)

    def delete_file(self):
        ''' Delete the real file-system representation of this model
        '''
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
    ''' Represents a similar grouping of bags
    '''
    name = models.CharField(max_length=256, null=False)
    description = models.TextField(default='')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f'{self.name} (Created by {self.created_by})'

class Bag(models.Model):
    ''' A bag created as a part of a user's submission
    '''
    bagging_date = models.DateTimeField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    part_of_group = models.ForeignKey(BagGroup, on_delete=models.SET_NULL, blank=True, null=True)
    bag_name = models.CharField(max_length=256, null=True)
    caais_metadata = models.TextField(default=r'{}')

    @property
    def location(self):
        ''' Get the location on the file system for this bag
        '''
        return os.path.join(BAG_STORAGE_FOLDER, self.user.username, self.bag_name)

    @property
    def transfer_info(self):
        ''' Exposes a small amount of information from the transfer to be shown
        for a user
        '''
        json_metadata = json.loads(self.caais_metadata)
        title = json_metadata['section_1']['accession_title']
        extent = json_metadata['section_3']['extent_statement'][0]['quantity_and_type_of_units']
        return {
            'title': title,
            'extent': extent,
        }

    def get_admin_change_url(self):
        ''' Get the URL to change this object in the admin
        '''
        view_name = 'admin:{0}_{1}_change'.format(self._meta.app_label, self._meta.model_name)
        return reverse(view_name, args=(self.pk,))

    def get_admin_zip_url(self):
        ''' Get the URL to start zipping this bag from the admin
        '''
        view_name = 'admin:{0}_{1}_zip'.format(self._meta.app_label, self._meta.model_name)
        return reverse(view_name, args=(self.pk,))

    def __str__(self):
        return self.bag_name


@receiver(pre_delete)
def delete_bag(sender, instance, **kwargs):
    ''' Delete the filesystem mirror of a Bag before the Bag is deleted from the
    database
    '''
    if sender == Bag:
        bag = instance
        if os.path.exists(bag.location) and os.path.isdir(bag.location):
            shutil.rmtree(bag.location)


class Submission(models.Model):
    ''' The top-level object representing a user's submission. This object has
    a user, a bag, and can have any number of appraisal statements linked to it
    '''
    class ReviewStatus(models.TextChoices):
        ''' The status of the bag's review
        '''
        NOT_REVIEWED = 'NR', _('Not Reviewed')
        REVIEW_STARTED = 'RS', _('Review Started')
        REVIEW_COMPLETE = 'RC', _('Review Complete')

    class LevelOfDetail(models.TextChoices):
        ''' The level of detail of the submission
        '''
        NOT_SPECIFIED = 'NS', _('Not Specified')
        MINIMAL = 'ML', _('Minimal')
        PARTIAL = 'PL', _('Partial')
        FULL = 'FL', _('Full')

    submission_date = models.DateTimeField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    bag = models.ForeignKey(Bag, on_delete=models.SET_NULL, null=True)
    review_status = models.CharField(max_length=2, choices=ReviewStatus.choices,
                                     default=ReviewStatus.NOT_REVIEWED)
    accession_identifier = models.CharField(max_length=128, default='', null=True)
    level_of_detail = models.CharField(max_length=2, choices=LevelOfDetail.choices,
                                       default=LevelOfDetail.NOT_SPECIFIED)

    def get_report(self):
        ''' Create an HTML report for this submission

        Returns:
            (str): A string containing the report markup
        '''
        return render_to_string('recordtransfer/report/metadata_report.html', context={
            'bag': self.bag,
            'current_date': timezone.now(),
            'metadata': json.loads(self.bag.caais_metadata),
        })

    def get_admin_change_url(self):
        ''' Get the URL to change this object in the admin
        '''
        view_name = 'admin:{0}_{1}_change'.format(self._meta.app_label, self._meta.model_name)
        return reverse(view_name, args=(self.pk,))

    def get_admin_report_url(self):
        ''' Get the URL to generate a report for this object in the admin
        '''
        view_name = 'admin:{0}_{1}_report'.format(self._meta.app_label, self._meta.model_name)
        return reverse(view_name, args=(self.pk,))

    def __str__(self):
        return f'Submission by {self.user} at {self.submission_date}'


class Appraisal(models.Model):
    ''' An appraisal made by an administrator for a submission
    '''
    class AppraisalType(models.TextChoices):
        ''' The type of the appraisal being made '''
        ARCHIVAL_APPRAISAL = 'AP', _('Archival Appraisal')
        MONETARY_APPRAISAL = 'MP', _('Monetary Appraisal')

    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    appraisal_type = models.CharField(max_length=2, choices=AppraisalType.choices)
    appraisal_date = models.DateTimeField()
    statement = models.TextField(null=False)
    note = models.TextField(default='', null=True)

    def __str__(self):
        return f'{self.get_appraisal_type_display()} by {self.user} on {self.appraisal_date}'


class Job(models.Model):
    ''' A background job executed by an admin user
    '''
    class JobStatus(models.TextChoices):
        ''' The status of the bag's review
        '''
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

    def get_admin_download_url(self):
        ''' Get the URL to download the attached file from the admin
        '''
        view_name = 'admin:{0}_{1}_download'.format(self._meta.app_label, self._meta.model_name)
        return reverse(view_name, args=(self.pk,))

    def __str__(self):
        return f'{self.name} (Created by {self.user_triggered})'


class Right(models.Model):
    ''' A term describing a right
    '''
    name = models.CharField(max_length=255, null=False, unique=True)
    description = models.CharField(max_length=255, null=False)

    def __str__(self):
        return self.name


class SourceType(models.Model):
    ''' A term describing a source type
    '''
    name = models.CharField(max_length=255, null=False, unique=True)
    description = models.CharField(max_length=255, null=False)

    def __str__(self):
        return self.name


class SourceRole(models.Model):
    ''' A term describing a source role
    '''
    name = models.CharField(max_length=255, null=False, unique=True)
    description = models.CharField(max_length=255, null=False)

    def __str__(self):
        return self.name
