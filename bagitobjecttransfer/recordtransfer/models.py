from datetime import datetime
import os

from django.db import models
from django.utils.crypto import get_random_string


class UploadSession(models.Model):
    token = models.CharField(max_length=32)
    started_at = models.DateTimeField()

    @classmethod
    def new_session(cls):
        return cls(token=get_random_string(length=32), started_at=datetime.now())

    def __str__(self):
        return f'{self.token} ({self.started_at})'


class UploadedFile(models.Model):
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


class AppUser(models.Model):
    name = models.CharField(max_length=256)
    email = models.CharField(max_length=256)

    def __str__(self):
        return f'{self.name}, {self.email}'


class Bag(models.Model):
    bagging_date = models.DateTimeField()
    bag_location = models.CharField(max_length=256)
    user = models.ForeignKey(AppUser, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f'"{self.bag_location}" bagged at {self.bagging_date} by {self.user.name}'

