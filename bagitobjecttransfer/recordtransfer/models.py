''' Record Transfer application models '''
from collections import OrderedDict
from pathlib import Path
from typing import Union
import os
import json
import logging
import shutil
import uuid

import bagit

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from recordtransfer import settings
from recordtransfer.caais import flatten_meta_tree
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


class Bag(models.Model):
    ''' A bag created as a part of a user's submission
    '''
    bagging_date = models.DateTimeField(null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    part_of_group = models.ForeignKey(BagGroup, on_delete=models.SET_NULL, blank=True, null=True)
    bag_name = models.CharField(max_length=256, null=True)
    caais_metadata = models.TextField(default=r'{}')
    upload_session = models.ForeignKey(UploadSession, null=True, on_delete=models.SET_NULL)
    uuid = models.UUIDField(default=uuid.uuid4)

    _json_metadata = None

    @property
    def json_metadata(self):
        ''' Returns caais_metadata as a python dict
        '''
        if not self._json_metadata:
            return json.loads(self.caais_metadata)
        return self._json_metadata

    @property
    def flat_json_metadata(self):
        return flatten_meta_tree(self.json_metadata)

    @property
    def user_folder(self):
        return os.path.join(settings.BAG_STORAGE_FOLDER, slugify(self.user.username))

    @property
    def location(self):
        ''' Get the location on the file system for this bag
        '''
        return os.path.join(self.user_folder, self.bag_name)

    @property
    def exists(self):
        return os.path.exists(self.location)

    @property
    def title(self):
        ''' Get title from caais_metadata

        Returns:
            (str): The title as it was captured in the transfer form
        '''
        title = None
        json_metadata = self.json_metadata
        if 'section_1' in json_metadata:
            title = json_metadata['section_1'].get('accession_title', None)
        return title or 'No title'

    @property
    def extent(self):
        ''' Get first extent statement from caais_metadata

        Returns:
            (str): The extent statement as it was created from the Bag's file
                uploads
        '''
        extent = None
        json_metadata = self.json_metadata
        if 'section_3' in json_metadata:
            statements = json_metadata['section_3'].get('extent_statement', [])
            if statements:
                extent = statements[0].get('quantity_and_type_of_units', None)
        return extent or 'No files'

    def update_metadata(self, metadata: dict):
        ''' Replace caais_metadata with a new serialized dictionary.

        Args:
            metadata (dict): The new dictionary to replace caais_metadata
        '''
        self.caais_metadata = json.dumps(metadata)
        self._json_metadata = None

    def update_accession_id(self, user, accession_id: str, commit=False):
        ''' Update the bag's accession identifier in Section 1 of the
        caais_metadata

        Args:
            user: The user making the request to update this bag
            accession_id (str): The new accession identifier
            commit (bool): True to save() the model post-change, False if not
        '''
        bag_metadata = self.json_metadata
        if 'section_1' in bag_metadata and 'accession_identifier' in bag_metadata['section_1']:
            curr_id = bag_metadata['section_1']['accession_identifier']
            if curr_id != accession_id:
                bag_metadata['section_1']['accession_identifier'] = accession_id
                self.update_metadata(bag_metadata)
                if curr_id:
                    note = 'Accession Identifier changed from {} to {}'.format(
                        curr_id, accession_id
                    )
                else:
                    note = 'Accession Identifier assigned to {}'.format(
                        accession_id
                    )
                self._log_new_event(user, 'Accession Identifier Changed', note, commit=commit)

    def update_level_of_detail(self, user, level_of_detail: str, commit=False):
        ''' Update the bag's level of detail in Section 7 of the caais_metadata

        Args:
            user: The user making the request to update this bag
            level_of_detail (str): The new level of detail
            commit (bool): True to save() the model post-change, False if not
        '''
        bag_metadata = self.json_metadata
        if 'section_7' in bag_metadata and 'level_of_detail' in bag_metadata['section_7']:
            curr_level = bag_metadata['section_7']['level_of_detail']
            if curr_level != level_of_detail:
                bag_metadata['section_7']['level_of_detail'] = level_of_detail
                self.update_metadata(bag_metadata)
                if curr_level:
                    note = 'Level of Detail changed from {} to {}'.format(
                        curr_level, level_of_detail
                    )
                else:
                    note = 'Level of Detail assigned to {}'.format(
                        level_of_detail
                    )
                self._log_new_event(user, 'Level of Detail Changed', note, commit=commit)

    def add_appraisal(self, user, appraisal, commit=False):
        ''' Add an Appraisal statement to the Bag in Section 4 of the
        caais_metadata. If an appraisal with the same ID already exists in the
        appraisal list, it is not added again.

        Args:
            user: The user making the request to update this bag
            appraisal (Appraisal): The new appraisal
            commit (bool): True to save() the model post-change, False if not
        '''
        bag_metadata = self.json_metadata
        if 'section_4' in bag_metadata:
            if 'appraisal_statement' not in bag_metadata['section_4']:
                bag_metadata['section_4']['appraisal_statement'] = []

            # Skip adding if appraisal already exists
            for existing in bag_metadata['section_4']['appraisal_statement']:
                if existing['_id'] == appraisal.id:
                    return

            new_appraisal = appraisal.to_serializable()
            bag_metadata['section_4']['appraisal_statement'].append(new_appraisal)
            self.update_metadata(bag_metadata)
            note = '{} with ID {} created by {} ({}) was added'.format(
                str(Appraisal.AppraisalType(appraisal.appraisal_type).label),
                appraisal.id, user.username, user.email
            )
            self._log_new_event(user, 'Appraisal Added', note, commit=commit)

    def remove_appraisal(self, user, appraisal, commit=False):
        ''' Remove an Appraisal statement from the Bag in Section 4 of the
        caais_metadata. If an appraisal with the same ID does not exist in the
        appraisal list, no appraisal is removed.

        One appraisal maximum is removed at a time with this method. If an
        appraisal was added multiple times by accident to the Bag or two or more
        appraisals were added with the same ID, call this method multiple times
        to remove each instance of the duplicate appraisal one-by-one.

        Args:
            user: The user making the request to update this bag
            appraisal (Appraisal): The new appraisal
            commit (bool): True to save() the model post-change, False if not
        '''
        bag_metadata = self.json_metadata
        if 'section_4' in bag_metadata and 'appraisal_statement' in bag_metadata['section_4']:
            i_del = -1
            for i, bag_appraisal in enumerate(bag_metadata['section_4']['appraisal_statement']):
                if bag_appraisal['_id'] == appraisal.id:
                    i_del = i
                    break
            if i_del != -1:
                del bag_metadata['section_4']['appraisal_statement'][i_del]
                self.update_metadata(bag_metadata)
                note = 'Appraisal with ID {} created by {} ({}) was deleted'.format(
                    appraisal.id, appraisal.user.username, appraisal.user.email
                )
                self._log_new_event(user, 'Appraisal Deleted', note, commit=commit)

    def _log_new_event(self, user, event_type: str, event_note: str, commit=False):
        ''' Create a new event in Section 5 of the caais_metadata.

        Args:
            user: The user making the request to change the bag
            event_type (str): The name of the event
            event_note (str): A note detailing what happened in the event
            commit (bool): True to save() the model post-change, False if not
        '''
        new_event = OrderedDict()
        now = timezone.localtime(timezone.now())
        new_event['event_type'] = event_type
        new_event['event_date'] = now.strftime(r'%Y-%m-%d %H:%M:%S %Z')
        new_event['event_agent'] = '{} ({})'.format(user.username, user.email)
        new_event['event_note'] = event_note
        bag_metadata = self.json_metadata
        bag_metadata['section_5']['event_statement'].append(new_event)
        self.update_metadata(bag_metadata)
        if commit:
            self.save()

    def make_bag(self, algorithms: Union[str, list] = 'sha512', file_perms: str = '644',
                 move_files: bool = True, logger=None):
        ''' Create a BagIt bag on the file system for this Bag. The location of the BagIt bag is
        determined by self.location. Checks the validity of the Bag post-creation to ensure that
        integrity is maintained. The data payload files come from the UploadSession associated with
        this Bag. Sets self.bagging_date if the BagIt bag is created.

        Args:
            algorithms (Union[str, list]): The algorithms to generate the BagIt bag with
            file_perms (str): A string-based octal "chmod" number
            move_files (bool): True to move uploaded files to the bag directory, False to create a
                copy of the files. If False, the file copies should be removed at a later time
            logger: A logger instance (optional)

        Returns:
            (dict): A dictionary containing the keys: bag_created - True if bag was created, False
                if not; bag_valid - True if created bag is valid, False if not; time_created - the
                time the bag was created, None if not created; missing_files - a list of files
                missing from the UploadSession, empty list if none missing
        '''
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

        if move_files:
            copied, missing = self.upload_session.move_session_uploads(self.location, logger)
        else:
            copied, missing = self.upload_session.copy_session_uploads(self.location, logger)

        if missing:
            LOGGER.error(msg=('One or more uploaded files is missing!'))
            LOGGER.info(msg=('Removing bag at "{0}" due to missing files'.format(self.location)))
            self.remove_bag()
            return {
                'missing_files': missing, 'bag_created': False, 'bag_valid': False,
                'time_created': None,
            }

        logger.info(msg=('Creating BagIt bag at "{0}"'.format(self.location)))
        logger.info(msg=('Using these checksum algorithm(s): {0}'.format(', '.join(algorithms))))

        bag = bagit.make_bag(self.location, self.flat_json_metadata, checksums=algorithms)

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
        self.bagging_date = current_time
        self.save()

        return {
            'missing_files': [], 'bag_created': True, 'bag_valid': True,
            'time_created': current_time,
        }

    def update_bag(self, logger=None):
        ''' Update the file system mirror of this Bag with the current metadata of this Bag. The
        integrity of the bag is checked before updating; if the bag is invalid, the bag will not be
        updated/

        Returns:
            (dict): A dictionary containing update information
        '''
        metadata = self.flat_json_metadata
        logger = logger or LOGGER
        bag_folder = self.location

        logger.info('Updating file system bag located at "%s"', bag_folder)

        if not os.path.exists(bag_folder):
            logger.error(msg=(
                'There is no bag located at "{0}"!'\
                .format(bag_folder)
            ))
            return {'bag_exists': False, 'bag_updated': False, 'num_fields_updated': 0}

        bag = bagit.Bag(bag_folder)

        # Expensive operation
        if not bag.is_valid():
            logger.error(msg=(
                'The bag located at "{0}" was found to be invalid!'\
                .format(bag_folder)
            ))
            return {'bag_exists': True, 'bag_valid': False, 'num_fields_updated': 0}

        if not metadata:
            logger.info(msg=(
                'No updates were made to the bag-info.txt for the bag at "{0}"'\
                .format(bag_folder)
            ))
            return {'bag_exists': True, 'bag_valid': True, 'num_fields_updated': 0}

        LOGGER.info(msg=('Updating bag-info.txt for the bag at "{0}"'.format(bag_folder)))
        fields_updated = 0
        for key, new_value in metadata.items():
            if key.startswith('_'):
                # Ignore hidden fields
                continue
            if key not in bag.info:
                logger.warning(msg=(
                    'New fields cannot be added to a bag. Found invalid field "{0}"'\
                    .format(key)
                ))
            elif bag.info[key] != new_value:
                bag.info[key] = new_value
                fields_updated += 1

        if fields_updated == 0:
            logger.info(msg=(
                'No updates were made to the bag-info.txt file for the bag at "{0}"'\
                .format(bag_folder)
            ))
            return {'bag_exists': True, 'bag_valid': True, 'num_fields_updated': fields_updated}

        # Don't re-create manifest for files, only for bag-info
        bag.save(manifests=False)

        if not bag.is_valid():
            logger.error(msg=(
                'Made {0} updates to the bag-info.txt file for the bag at "{1}", but the saved '
                'bag was invalid!'\
                .format(fields_updated, bag_folder)
            ))
            return {'bag_exists': True, 'bag_valid': False, 'num_fields_updated': fields_updated}

        logger.info(msg=(
            'Made {0} updates to the bag-info.txt file for the bag at "{1}"'\
            .format(fields_updated, bag_folder)
        ))
        return {'bag_exists': True, 'bag_valid': True, 'num_fields_updated': fields_updated}

    def remove_bag(self):
        ''' Remove the BagIt bag from the file system associated with this Bag
        '''
        self.upload_session.remove_session_uploads()
        if os.path.exists(self.location) and os.path.isdir(self.location):
            shutil.rmtree(self.location)

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

@receiver(pre_save)
def update_location(sender, instance, *args, **kwargs):
    ''' Update location in caais_metadata prior to saving
    '''
    if sender == Bag:
        bag = instance
        metadata = bag.json_metadata
        default_location = settings.DEFAULT_DATA.get('section_4', {}).get('storage_location', '')
        current_location = metadata.get('section_4', {}).get('storage_location', '')
        if not current_location or current_location == default_location:
            if 'section_4' not in metadata:
                metadata['section_4'] = {}
            metadata['section_4']['storage_location'] = bag.location
            bag.update_metadata(metadata)

@receiver(pre_delete)
def delete_bag(sender, instance, **kwargs):
    ''' Delete the filesystem mirror of a Bag before the Bag is deleted from the
    database
    '''
    if sender == Bag:
        bag = instance
        bag.remove_bag()


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
    bag = models.OneToOneField(Bag, on_delete=models.SET_NULL, null=True, related_name='submission')
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
