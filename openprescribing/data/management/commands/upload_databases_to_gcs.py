# This script uploads the databases from the data app to Google Cloud Storage, to allow
# them to be downloaded for local analysis and development by members of the team who
# don't have SSH keys.
#
# The databases are uploaded to the databases folder of the openprescribing bucket.
# This bucket belongs to the openprescribing2 project (openprescribing was taken).
#
# The script expects an environment variable called GOOGLE_APPLICATION_CREDENTIALS,
# which points to the path of a JSON file containing key for a service account with the
# `storage.objectUser` role.
#
# To create the bucket/service account/key I ran:
#
#   gcloud storage buckets create gs://openprescribing \
#     --project=openprescribing2 \
#     --location=europe-west2 \
#     --uniform-bucket-level-access
#   gcloud iam service-accounts create database-uploader \
#     --project=openprescribing2
#   gcloud storage buckets add-iam-policy-binding gs://openprescribing \
#     --member=serviceAccount:database-uploader@openprescribing2.iam.gserviceaccount.com \
#     --role=roles/storage.objectUser
#   gcloud iam service-accounts keys create database-uploader.json \
#     --iam-account=database-uploader@openprescribing2.iam.gserviceaccount.com
#
# The script is run by a dokku cron job specified in app.json.  It is configured to run
# four hours after the nightly import, which seems to be long enough to allow for the
# biggest dataset (the prescribing data) to be fetched and ingested.
#
# The script does not have automated tests, because the costs of mocking the GCS client
# outweigh the benefits of any confidence we'd get from the tests.

# pragma: no cover file

import base64
import hashlib
import logging
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from google.cloud import storage

from openprescribing.data.utils.sqlite_utils import ensure_main_database_file_is_updated


GCS_PROJECT = "openprescribing2"
GCS_BUCKET = "openprescribing"
GCS_PREFIX = "databases"

log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Upload database files to Google Cloud Storage"

    def handle(self, *args, **options):
        ensure_main_database_file_is_updated()

        client = storage.Client(project=GCS_PROJECT)
        bucket = client.bucket(GCS_BUCKET)

        for database_path in [settings.PRESCRIBING_DATABASE, settings.SQLITE_DATABASE]:
            object_name = f"{GCS_PREFIX}/{database_path.name}"
            blob = bucket.blob(object_name)
            if get_remote_file_md5_hash(blob) == get_local_file_md5_hash(database_path):
                log.info(f"skipping: {database_path}")
            blob.upload_from_filename(database_path)
            log.info(f"uploaded: {database_path}")


def get_local_file_md5_hash(path):
    digest = hashlib.md5(usedforsecurity=False)
    with Path(path).open("rb") as f:
        while chunk := f.read(1024 * 1024):
            digest.update(chunk)
    return base64.b64encode(digest.digest()).decode("ascii")


def get_remote_file_md5_hash(blob):
    try:
        blob.reload()
    except Exception as exc:
        if exc.__class__.__name__ != "NotFound":
            raise
        return None

    return blob.md5_hash
