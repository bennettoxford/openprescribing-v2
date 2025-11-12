import datetime

from django.db import models


class IngestedFile(models.Model):
    "Track the latest file we've ingested for each dataset"

    class Meta:
        db_table = "ingested_file"

    dataset_name = models.TextField(primary_key=True)
    filename = models.TextField()
    last_modified = models.DateTimeField()

    @classmethod
    def get_by_name(cls, dataset_name):
        try:
            return cls.objects.get(dataset_name=dataset_name).filename
        except cls.DoesNotExist:
            # It simplifies the check-for-updates logic if we return a default value
            # here. The empty string works because it's the smallest string and so any
            # other file will compare greater than it, which is the behaviour we want.
            return ""

    @classmethod
    def set_by_name(cls, dataset_name, filename):
        # Recording the timestamp lets us easily check when each dataset was last
        # ingested
        now = datetime.datetime.now(datetime.UTC)
        cls(dataset_name=dataset_name, filename=filename, last_modified=now).save()
