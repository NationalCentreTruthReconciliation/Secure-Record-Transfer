from django.contrib import admin

from recordtransfer.models import Bag, UploadSession, UploadedFile

admin.site.register(Bag)
admin.site.register(UploadedFile)
admin.site.register(UploadSession)
