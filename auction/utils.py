import PIL
import os
from uuid import uuid4
from PIL import Image


def path_and_rename(instance, filename):
    upload_to = 'images'
    ext = filename.split('.')[-1]
    # get filename
    if instance.pk:
        filename = f"{instance.pk}.{ext}"
    else:
        # set filename as random string
        filename = f"{uuid4().hex}.{ext}"
    # return the whole path to the file
    return os.path.join(upload_to, filename)