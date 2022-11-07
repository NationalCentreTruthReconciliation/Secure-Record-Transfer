''' Record Transfer application models '''
import os
from collections import OrderedDict
from pathlib import Path
import json
import logging
import shutil
import uuid
from typing import Union

import bagit
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from caais.export import ExportVersion
from caais.models import Metadata
from recordtransfer import settings
from recordtransfer.storage import OverwriteStorage, UploadedFileStorage


LOGGER = logging.getLogger(__name__)


class User(AbstractUser):
    ''' The main User object used to authenticate users
    '''
    gets_bag_email_updates = models.BooleanField(default=False)
    confirmed_email = models.BooleanField(default=False)
    gets_notification_emails = models.BooleanField(default=True)

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

    @property
    def upload_size(self):
        ''' Get total size (in bytes) of all uploaded files in this session
        '''
        return sum(f.file_upload.size for f in self.get_existing_file_set())

    def get_existing_file_set(self):
        ''' Get all files from the uploadedfile_set where the file exists
        '''
        return [f for f in self.uploadedfile_set.all() if f.exists]

    def number_of_files_uploaded(self):
        ''' Get the number of files associated with this session.

        Returns:
            (int): The number of files
        '''
        return len(self.uploadedfile_set.all())

    def remove_session_uploads(self, logger=None):
        ''' Remove uploaded files associated with this session.

        Args:
            logger: A logger object
        '''
        logger = logger or LOGGER
        existing_files = self.get_existing_file_set()
        if not existing_files:
            logger.info(msg=(
                'There are no existing uploaded files in the session {0}'\
                .format(self.token)
            ))
        else:
            logger.info(msg=(
                'Removing {0} uploaded files from the session {1}'\
                .format(len(existing_files), self.token)
            ))
            for uploaded_file in existing_files:
                uploaded_file.remove()

    def move_session_uploads(self, destination, logger=None):
        ''' Move uploaded files associated with this session to a destination directory.

        Args:
            destination (str): The destination directory
            logger: A logger object

        Returns:
            (tuple): A two tuple containing a list of the copied, and missing files
        '''
        return self._copy_session_uploads(destination, delete=True, logger=logger)

    def copy_session_uploads(self, destination, logger=None):
        ''' Copy uploaded files associated with this session to a destination directory. Files are
        not removed from their original location.

        Args:
            destination (str): The destination directory
            logger: A logger object

        Returns:
            (tuple): A two tuple containing a list of the copied, and missing files
        '''
        return self._copy_session_uploads(destination, delete=False, logger=logger)

    def _copy_session_uploads(self, destination, delete=True, logger=None):
        logger = logger or LOGGER

        destination_path = Path(destination)
        if not destination_path.exists():
            message = 'The destination path {0} does not exist!'
            logger.error(msg=message.format(destination))
            raise FileNotFoundError(message.format(destination))

        files = self.uploadedfile_set.all()

        if not files:
            logger.warning(msg=('No existing files found in the session {0}'.format(self.token)))
            return ([], [])

        verb = 'Moving' if delete else 'Copying'
        logger.info(msg=('{0} {1} temp files to {2}'.format(verb, len(files), destination)))
        copied = []
        missing = []
        for uploaded_file in files:
            source_path = uploaded_file.file_upload.path

            if not uploaded_file.exists:
                logger.error(msg=('File "{0}" was moved or deleted'.format(source_path)))
                missing.append(str(source_path))
                continue

            new_path = destination_path / uploaded_file.name
            logger.info(msg=('{0} {1} to {2}'.format(verb, source_path, new_path)))

            if delete:
                uploaded_file.move(new_path)
            else:
                uploaded_file.copy(new_path)

            copied.append(str(new_path))

        return (copied, missing)

    def __str__(self):
        return f'{self.token} ({self.started_at})'


def session_upload_location(instance, filename):
    if instance.session:
        return '{0}/{1}'.format(instance.session.token, filename)
    return 'NOSESSION/{0}'.format(filename)

class UploadedFile(models.Model):
    ''' Represents a file that a user uploaded during an upload session
    '''
    name = models.CharField(max_length=256, null=True, default='-')
    session = models.ForeignKey(UploadSession, on_delete=models.CASCADE, null=True)
    file_upload = models.FileField(null=True,
                                   storage=UploadedFileStorage,
                                   upload_to=session_upload_location)

    @property
    def exists(self):
        ''' Determine if the file this object represents exists on the file system.

        Returns:
            (bool): True if file exists, False otherwise
        '''
        return self.file_upload and self.file_upload.storage.exists(self.file_upload.name)

    def copy(self, new_path):
        ''' Copy this file to a new path.

        Args:
            new_path: The new path to copy this file to
        '''
        if self.file_upload:
            shutil.copy2(self.file_upload.path, new_path)

    def move(self, new_path):
        ''' Move this file to a new path. Marks this file as removed post-move.

        Args:
            new_path: The new path to move this file to
        '''
        if self.file_upload:
            shutil.move(self.file_upload.path, new_path)
            self.remove()

    def remove(self):
        ''' Delete the real file-system representation of this model.
        '''
        if self.file_upload:
            self.file_upload.delete(save=True)

    def __str__(self):
        if self.exists:
            return f'{self.name} | Session {self.session}'
        return f'{self.name} Removed! | Session {self.session}'


class BagGroup(models.Model):
    ''' Represents a similar grouping of bags
    '''
    name = models.CharField(max_length=256, null=False)
    description = models.TextField(default='')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    @property
    def number_of_bags_in_group(self):
        return len(self.bag_set.all())

    def __str__(self):
        return f'{self.name} ({self.created_by})'


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

    submission_date = models.DateTimeField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    bag = models.OneToOneField(Metadata, on_delete=models.CASCADE, null=True, related_name='submission')
    review_status = models.CharField(max_length=2, choices=ReviewStatus.choices,
                                     default=ReviewStatus.NOT_REVIEWED)
    part_of_group = models.ForeignKey(BagGroup, on_delete=models.SET_NULL, blank=True, null=True)
    upload_session = models.ForeignKey(UploadSession, null=True, on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid.uuid4)
    bag_name = models.CharField(max_length=256, null=True)

    @property
    def user_folder(self):
        return os.path.join(settings.BAG_STORAGE_FOLDER, slugify(self.user.username))

    @property
    def location(self):
        """ Get the location on the file system for this bag
        """
        return os.path.join(self.user_folder, self.bag_name)

    @property
    def extent_statements(self):
        """ Return the first extent statement for this submission. """
        for e in self.bag.extent_statements.get_queryset().all():
            return e.quantity_and_type_of_units
        return ''

    def get_report(self):
        ''' Create an HTML report for this submission

        Returns:
            (str): A string containing the report markup
        '''
        report_metadata = self.bag.get_caais_metadata()
        report_metadata['section_1']['status'] = self.ReviewStatus(self.review_status).label
        report_metadata['section_4']['appraisal_statement'] = self.appraisals.get_caais_metadata()
        return render_to_string('recordtransfer/report/metadata_report.html', context={
            'submission': self,
            'current_date': timezone.now(),
            'metadata': report_metadata,
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

    def get_admin_zip_url(self):
        """ Get the URL to generate a zipped bag for this object in the admin """
        view_name = f'admin:{self._meta.app_label}_{self._meta.model_name}_zip'
        return reverse(view_name, args=(self.pk,))

    def __str__(self):
        return f'Submission by {self.user} at {self.submission_date}'

    def flatten(self, version: ExportVersion = ExportVersion.CAAIS_1_0):
        new_row = self.bag.flatten(version)
        new_row['status'] = self.ReviewStatus(self.review_status).label if self.review_status else ''
        new_row.update(self.appraisals.flatten(version))
        return new_row

    def make_bag(self, algorithms: Union[str, list] = 'sha512', file_perms: str = '644',
                 move_files: bool = True, logger=None):
        """ Create a BagIt bag on the file system for this Submission. The location of the BagIt bag is
        determined by self.location. Checks the validity of the Bag post-creation to ensure that
        integrity is maintained. The data payload files come from the UploadSession associated with
        this Bag. Sets self.bagging_date if the BagIt bag is created.

        Args:
            algorithms (Union[str, list]): The algorithms to generate the BagIt bag with
            file_perms (str): A string-based octal "chmod" number
            move_files (bool): True to move uploaded files to the bag directory, False to create a
                copy of the files. If False, the file copies should be removed at a later time
            logger: A logger instance (optional)
        """
        logger = logger or LOGGER

        if not algorithms:
            raise ValueError('algorithms cannot be empty')

        if isinstance(algorithms, str):
            algorithms = [a.strip() for a in algorithms.split(',')]

        for algorithm in algorithms:
            if algorithm not in bagit.CHECKSUM_ALGOS:
                raise ValueError('{0} is not a valid checksum algorithm'.format(algorithm))

        if not os.path.exists(settings.BAG_STORAGE_FOLDER) or \
                not os.path.isdir(settings.BAG_STORAGE_FOLDER):
            LOGGER.error(msg=(
                'The BAG_STORAGE_FOLDER "{0}" does not exist!'.format(settings.BAG_STORAGE_FOLDER)
            ))
            return {
                'missing_files': [], 'bag_created': False, 'bag_valid': False,
                'time_created': None
            }

        if not os.path.exists(self.user_folder) or not os.path.isdir(self.user_folder):
            os.mkdir(self.user_folder)
            LOGGER.info(msg=('Created new user folder at "{0}"'.format(self.user_folder)))

        if os.path.exists(self.location):
            LOGGER.warning(msg=('A bag already exists at "{0}"'.format(self.location)))
            return {
                'missing_files': [], 'bag_created': False, 'bag_valid': False,
                'time_created': None
            }

        os.mkdir(self.location)
        LOGGER.info(msg=('Created new bag folder at "{0}"'.format(self.user_folder)))

        copied, missing = self.upload_session.copy_session_uploads(self.location, logger)

        if missing:
            LOGGER.error(msg='One or more uploaded files is missing!')
            LOGGER.info(msg=('Removing bag at "{0}" due to missing files'.format(self.location)))
            self.remove_bag()
            return {
                'missing_files': missing, 'bag_created': False, 'bag_valid': False,
                'time_created': None,
            }

        logger.info(msg=('Creating BagIt bag at "{0}"'.format(self.location)))
        logger.info(msg=('Using these checksum algorithm(s): {0}'.format(', '.join(algorithms))))

        bagit_info = self.bag.flatten()
        bagit_info.update(self.appraisals.flatten())
        bag = bagit.make_bag(self.location, bagit_info, checksums=algorithms)

        logger.info(msg=('Setting file mode for bag payload files to {0}'.format(file_perms)))
        perms = int(file_perms, 8)
        for payload_file in bag.payload_files():
            payload_file_path = os.path.join(self.location, payload_file)
            os.chmod(payload_file_path, perms)

        logger.info(msg=('Validating the bag created at "{0}"'.format(self.location)))
        valid = bag.is_valid()

        if not valid:
            logger.error(msg='Bag is INVALID!')
            logger.info(msg=('Removing bag at "{0}" since it\'s invalid'.format(self.location)))
            self.remove_bag()
            return {
                'missing_files': [], 'bag_created': False, 'bag_valid': False,
                'time_created': None,
            }

        logger.info(msg='Bag is VALID')
        current_time = timezone.now()

        return {
            'missing_files': [], 'bag_created': True, 'bag_valid': True,
            'time_created': current_time,
        }

    def remove_bag(self):
        """ Remove the BagIt bag if it exists. """
        if os.path.exists(self.location):
            os.unlink(self.location)


class AppraisalManager(models.Manager):
    """ Custom manager for Appraisals """

    def flatten(self, version: ExportVersion = ExportVersion.CAAIS_1_0):
        if self.get_queryset().count() == 0:
            return {}

        appraisal_types = []
        appraisal_values = []
        appraisal_notes = []
        for appraisal in self.get_queryset().all():
            appraisal_types.append(appraisal.appraisal_type)
            appraisal_values.append(appraisal.statement)
            appraisal_notes.append(appraisal.note or 'NULL')

        if version == ExportVersion.CAAIS_1_0:
            return {
                'appraisalStatementType': '|'.join(appraisal_types),
                'appraisalStatementValue': '|'.join(appraisal_values),
                'appraisalStatementNote': '|'.join(appraisal_notes),
            }
        else:
            return {
                'appraisal': '|'.join([
                    f'Appraisal Type: {x}; Statement: {y}; Notes: {z}' if z != 'NULL' else
                    f'Appraisal Type: {x}; Statement: {y}' for
                    x, y, z in zip(appraisal_types, appraisal_values, appraisal_notes)
                ])
            }

    def get_caais_metadata(self):
        appraisals = []
        for appraisal in self.get_queryset().all():
            appraisals.append({
                'appraisal_statement_type': Appraisal.AppraisalType(appraisal.appraisal_type).label,
                'appraisal_statement_value': appraisal.statement,
                'appraisal_statement_note':  appraisal.note,
            })
        return appraisals


class Appraisal(models.Model):
    ''' An appraisal made by an administrator for a submission
    '''
    class AppraisalType(models.TextChoices):
        ''' The type of the appraisal being made '''
        ARCHIVAL_APPRAISAL = 'AP', _('Archival Appraisal')
        MONETARY_APPRAISAL = 'MP', _('Monetary Appraisal')

    objects = AppraisalManager()

    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='appraisals')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    appraisal_type = models.CharField(max_length=2, choices=AppraisalType.choices)
    appraisal_date = models.DateTimeField(auto_now=True)
    statement = models.TextField(null=False)
    note = models.TextField(default='', null=True)

    def to_serializable(self):
        obj = OrderedDict()
        obj['_id'] = self.id
        obj['appraisal_statement_type'] = str(self.AppraisalType(self.appraisal_type).label)
        obj['appraisal_statement_value'] = str(self.statement)
        obj['appraisal_statement_note'] = str(self.note)
        return obj

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


class SavedTransfer(models.Model):
    """ A saved transfer """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    last_updated = models.DateTimeField(unique=True)
    current_step = models.CharField(max_length=20, null=False)
    step_data = models.BinaryField(default=b'')

    def __str__(self):
        return f"Transfer of {self.last_updated} by {self.user}"
