from django.conf import settings
from django.db import models
from django.core.files.storage import FileSystemStorage
from fields import JSONField


UPLOAD_DIR=getattr(settings, 'UNAUTH_POSTING_ROOT', '%s/upfiles' % settings.MEDIA_ROOT)

# Create your models here.
class SavedRequest(models.Model):
    data = JSONField()
    key = models.BigIntegerField()

fs = FileSystemStorage(location=UPLOAD_DIR)
class SavedRequestFile(models.Model):
    request = models.ForeignKey(SavedRequest, related_name='files')
    name = models.CharField(max_length=500)
    content_type = models.CharField(max_length=100)
    file = models.FileField(upload_to="dummy", storage=fs)