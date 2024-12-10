"""Application-specific settings for the recordtransfer app."""

from decouple import config

from recordtransfer.configuration import AcceptedFileTypes

# The location where bags will be stored

BAG_STORAGE_FOLDER = config("BAG_STORAGE_FOLDER")

# The location where uploaded files are stored temporarily

UPLOAD_STORAGE_FOLDER = config("UPLOAD_STORAGE_FOLDER")

# File types allowed to be uploaded. See documentation for how to customize this list.

ACCEPTED_FILE_FORMATS = config(
    "ACCEPTED_FILE_TYPES",
    cast=AcceptedFileTypes(),
    default="Archive:zip|Audio:mp3,wav,flac|Document:docx,odt,pdf,txt,html|Image:jpg,jpeg,png,gif|Spreadsheet:xlsx,csv|Video:mkv,mp4",
)
