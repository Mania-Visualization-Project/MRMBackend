import os

from django.db import models
from django.utils import timezone

from MRMBackend import settings


class ManiaFile(models.Model):
    file_id = models.AutoField(primary_key=True)
    file_type = models.CharField(max_length=16)
    file_name = models.CharField(max_length=256)
    save_time = models.DateTimeField()
    ip = models.TextField(null=True)

    def get_dirname(self):
        path = os.path.join(settings.FILE_ROOT, str(self.file_id))
        if not os.path.isdir(path):
            os.makedirs(path)
        return path

    def get_path(self):
        return os.path.join(self.get_dirname(), str(self.file_name))


class Task(models.Model):
    task_id = models.AutoField(primary_key=True)
    status = models.TextField()  # ['queue', 'processing', 'finish', 'error']
    error_reason = models.TextField(null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True)
    activate_time = models.DateTimeField(null=True)
    extras = models.TextField()
    ip = models.TextField(null=True)
    beatmap_file = models.ForeignKey(ManiaFile, on_delete=models.CASCADE, related_name='map')
    replay_file = models.ForeignKey(ManiaFile, on_delete=models.CASCADE, related_name='replay')
    music_file = models.ForeignKey(ManiaFile, on_delete=models.CASCADE, related_name='music',
                                   null=True, blank=True)

    def get_dirname(self):
        path = os.path.join(settings.WORKING_ROOT, str(self.task_id))
        if not os.path.isdir(path):
            os.makedirs(path)
        return path

    def get_output_name(self):
        dirname = self.get_dirname()
        lst = list(filter(lambda x: x.endswith("mp4"), os.listdir(dirname)))
        if len(lst) > 0:
            return lst[0]
        return None

    def set_to_error(self, reason):
        self.status = "error"
        self.error_reason = reason
        self.end_time = timezone.now()
        err_path = os.path.join(self.get_dirname(), "error.txt")
        if not os.path.exists(err_path):
            with open(err_path, "w") as f:
                f.write(reason)


class Event(models.Model):
    event_id = models.AutoField(primary_key=True)
    event_type = models.TextField()
    event_message = models.TextField()
    time = models.DateTimeField(null=True, auto_now=True)