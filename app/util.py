import multiprocessing
import shutil
import os

from django.http import *
from django.utils import timezone

from MRMBackend import settings
from .models import Task, Event, ManiaFile
from .worker import start_render


def start_render_process(request):
    p = multiprocessing.Process(target=start_render,
                                args=(settings.SECRET_KEY,
                                      '{scheme}://{host}/{prefix}api/'.format(
                                          scheme=request.scheme,
                                          host=request.get_host(),
                                          prefix=settings.URL_PREFIX),
                                      settings.MRM_PATH))
    p.start()


last_check_time = None
last_clean_time = None


def check_too_long_task(request: HttpRequest):
    global last_check_time

    if last_check_time is not None and (timezone.now() - last_check_time).seconds <= 60:
        return
    last_check_time = timezone.now()
    print("Start to check too long task", last_check_time)

    processing_tasks = list(Task.objects.filter(status="processing"))
    if len(processing_tasks) == 0:
        return

    has_too_long_task = False
    now = timezone.now()

    for task in processing_tasks:
        offset = (now - task.start_time).seconds
        if offset >= 1800:
            task.set_to_error("time out")
            task.save(force_update=True)
            has_too_long_task = True

    if has_too_long_task:
        start_render_process(request)


def clean():
    global last_clean_time

    if last_clean_time is not None and (timezone.now() - last_clean_time).seconds <= 3600:
        return
    print("Start to clean old files", last_clean_time)
    last_clean_time = timezone.now()
    current = timezone.now()

    for task in Task.objects.all():
        dirname = task.get_dirname()
        if not os.path.isdir(dirname):
            continue
        if (current - task.start_time).total_seconds() >= 24 * 3600:
            Event(event_type="clean_task", event_message="id=%d" % task.task_id).save()
            shutil.rmtree(dirname)

    for mania_file in ManiaFile.objects.all():
        dirname = mania_file.get_dirname()
        if not os.path.isdir(dirname):
            continue
        if (current - mania_file.save_time).total_seconds() >= 24 * 3600:
            shutil.rmtree(dirname)
            Event(event_type="clean_file",
                  event_message="id=%d, type=%s" % (
                  mania_file.file_id, mania_file.file_type)).save()
