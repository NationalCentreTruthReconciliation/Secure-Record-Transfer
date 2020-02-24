from django.db import models

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
