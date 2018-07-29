from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class PrivateMediaStorage(FileSystemStorage):
    def __init__(self, *args, **kwargs):
        super().__init__(settings.PRIVATE_MEDIA_ROOT, *args, **kwargs)
