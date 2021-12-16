import multiprocessing
import shutil
import os
import datetime
import json

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

def parse_task_extra(task_dir):
    extra_file = os.path.join(task_dir, "task_extra.json")
    warning = {"is_music_mismatch": False, "is_replay_mismatch": False}
    if os.path.exists(extra_file):
        return json.load(open(extra_file))
    render_log = os.path.join(task_dir, "render.log")
    if not os.path.exists(render_log):
        return warning
    render_file = open(render_log, "r")
    count = 0
    while count <= 30:
        count += 1
        line = render_file.readline()
        if line.startswith("WARNING: Music given in the map") or line.startswith("警告：谱面的音乐文"):
            warning['is_music_mismatch'] = True
        elif line.startswith("WARNING: The beatmap cannot match the") or line.startswith("警告：谱面和回放文件"):
            warning['is_replay_mismatch'] = True
    if count >= 30:
        with open(extra_file, "w") as w:
            json.dump(warning, w)
    return warning


def clean():
    global last_clean_time

    if last_clean_time is not None and (timezone.now() - last_clean_time).seconds <= 3600:
        return
    print("Start to clean old files", last_clean_time)
    last_clean_time = timezone.now()
    current = timezone.now()

    for task in Task.objects.filter(start_time__range=(
            current - datetime.timedelta(days=7),
            current - datetime.timedelta(days=1),
    )):
        print(task)
        dirname = task.get_dirname(create=False)
        if not os.path.isdir(dirname):
            continue
        if (current - task.start_time).total_seconds() >= 24 * 3600:
            Event(event_type="clean_task", event_message="id=%d" % task.task_id).save()
            shutil.rmtree(dirname)

    for mania_file in ManiaFile.objects.filter(save_time__range=(
            current - datetime.timedelta(days=7),
            current - datetime.timedelta(days=1),
    )):
        print(mania_file)
        dirname = mania_file.get_dirname(create=False)
        if not os.path.isdir(dirname):
            continue
        if (current - mania_file.save_time).total_seconds() >= 24 * 3600:
            shutil.rmtree(dirname)
            Event(event_type="clean_file",
                  event_message="id=%d, type=%s" % (
                  mania_file.file_id, mania_file.file_type)).save()


def parse_game_mode_from_replay(replay_name):
    print("parse_game_mode_from_replay" + replay_name)
    if replay_name.endswith('.mr'):
        return "malody:key"
    if replay_name.endswith(".osr"):
        if 'Taiko' in replay_name:
            return "osu!taiko"
        if 'OsuMania' in replay_name:
            return "osu!mania"
        return "osu!mania"
    return "??"