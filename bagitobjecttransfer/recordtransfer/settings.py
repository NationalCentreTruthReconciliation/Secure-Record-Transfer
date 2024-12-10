"""Application-specific settings for the recordtransfer app."""

from decouple import config


# The location where bags will be stored

BAG_STORAGE_FOLDER = config("BAG_STORAGE_FOLDER")

# The location where uploaded files are stored temporarily

UPLOAD_STORAGE_FOLDER = config("UPLOAD_STORAGE_FOLDER")
