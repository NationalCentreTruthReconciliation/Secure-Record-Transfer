from django.db import models

class UploadedFile(models.Model):
    name = models.CharField(max_length=256)
    path = models.CharField(max_length=256)
    date_uploaded = models.DateTimeField()
    old_copy_removed = models.BooleanField()

    def __str__(self):
        if self.old_copy_removed:
            return f'{self.path}, uploaded at {self.date_uploaded}. File has been deleted.'
        else:
            return f'{self.path}, uploaded at {self.date_uploaded}. File has NOT been deleted.'


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
