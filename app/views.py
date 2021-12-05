# Create your views here.
import json
import os
import time
import datetime

import user_agents
from django.http import *
from django.utils import timezone
from django.views.decorators.csrf import *
from django.views.decorators.http import require_http_methods

from MRMBackend import settings
from . import util
from .models import ManiaFile, Task, Event, Report


class MessageException(Exception):
    def __init__(self, msg):
        self.msg = msg


def get_ip(request: HttpRequest):
    if "HTTP_X_FORWARDED_FOR" in request.META:
        return request.META["HTTP_X_FORWARDED_FOR"]
    return request.META.get("REMOTE_ADDR", None)


def get_user_agent(request: HttpRequest):
    return request.META.get("HTTP_USER_AGENT", "NO_USER_AGENT")


def record_crash():
    import traceback
    msg = traceback.format_exc()
    Event(event_type="crash", event_message=msg).save()
    return msg


def is_cn(request: HttpRequest):
    try:
        accept_language = request.META.get("HTTP_ACCEPT_LANGUAGE", "").replace(" ", "")
        for l in accept_language.split(","):
            if 'zh;q=' in l and float(l.replace("zh;q=", "")) >= 0.5:
                return True
    except:
        record_crash()
        return False


def on_error(exception: Exception):
    if type(exception) == MessageException:
        msg = exception.msg
        if "generated file fail" in msg:
            status = "render_failed"
        elif "Cannot find the beatmap with the given" in msg:
            status = "beatmap_not_found"
        elif "Invalid beatmap file" in msg or "Invalid .mc file" in msg:
            status = "beatmap_invalid"
        elif "Invalid replay file" in msg or "not a valid .mr file" in msg:
            status = "replay_invalid"
        elif "connection close" in msg:
            status = "time_exceeded"
        else:
            status = "error"
    else:
        msg = record_crash()
        status = "error"
    return JsonResponse({"status": status, "error_message": msg})


def on_success(obj: dict):
    return JsonResponse({"status": "OK", "error_message": "", "data": obj})


def check_param(key: str, container: dict, range=None, required_type=None):
    if key not in container:
        raise MessageException("'%s' params required!" % (key))
    val = container[key]
    if range is not None and val not in range:
        raise MessageException(
            "'%s' value in param '%s' should only be in %s!" % (str(val), key, str(range)))
    if required_type is not None:
        try:
            required_type(val)
        except:
            raise MessageException(
                "'%s' value in param '%s' requires type %s!!" % (str(val), key, str(required_type)))
    return val


@csrf_exempt
@require_http_methods("POST")
def upload(request: HttpRequest):
    try:
        obj = check_param('file', request.FILES)
        file_type = check_param('type', request.POST, range=["map", "replay", "bgm"])
        name = obj.name

        maniaFile = ManiaFile(file_type=file_type, file_name=name,
                              save_time=timezone.now(), ip=get_ip(request))
        maniaFile.save()

        with open(maniaFile.get_path(), 'wb') as f:
            for line in obj.chunks():
                f.write(line)
        return on_success({"file_id": str(maniaFile.file_id)})

    except Exception as e:
        return on_error(e)


@csrf_exempt
@require_http_methods("POST")
def generate(request: HttpRequest):
    def check_file_type(mania_file, require_type):
        if mania_file.file_type != require_type:
            raise MessageException("File id %s requires the type %s, but gets %s" % (
                mania_file.file_id, require_type, mania_file.file_type))

    try:
        data = json.load(request)
        map_id = check_param("map", data, required_type=int)
        map_file = ManiaFile.objects.get(file_id=int(map_id))
        check_file_type(map_file, "map")
        if "bgm" in data:
            bgm_id = check_param("bgm", data, required_type=int)
            bgm_file = ManiaFile.objects.get(file_id=int(bgm_id))
            check_file_type(bgm_file, "bgm")
        else:
            bgm_file = None
        replay_id = check_param("replay", data, required_type=int)
        replay_file = ManiaFile.objects.get(file_id=int(replay_id))
        check_file_type(replay_file, "replay")
        extras = check_param("extra", data, required_type=dict)

        task = Task(status="queue", start_time=timezone.now(), extras=json.dumps(extras),
                    beatmap_file=map_file, replay_file=replay_file, music_file=bgm_file,
                    ip=get_ip(request), activate_time=timezone.now(), environment=json.dumps({
                "ua": get_user_agent(request)
            }))
        task.save()

        util.start_render_process(request)

        return on_success({"task_id": str(task.task_id)})

    except Exception as e:
        return on_error(e)


@csrf_exempt
@require_http_methods("GET")
def query(request: HttpRequest):
    try:
        task_id = check_param("task_id", request.GET, required_type=int)
        task = Task.objects.get(task_id=int(task_id))

        util.check_too_long_task(request)

        # queue, processing, finish, error
        if task.status == "queue":
            running_count = len(list(Task.objects.filter(status="processing")))
            task.activate_time = timezone.now()
            task.save(force_update=True)
            return on_success({"type": "queue", "count": running_count})
        if task.status == "processing":
            path = os.path.join(task.get_dirname(), "progress.txt")
            progress = 0.0
            if os.path.exists(path):
                for retry in range(3):
                    try:
                        progress = float(open(path).readlines()[0].strip())
                        break
                    except:
                        time.sleep(0.1)
                        pass
            return on_success({"type": "processing", "progress": progress,
                               "__extra__": util.parse_task_extra(task.get_dirname())})
        if task.status == "finish":
            return on_success({"type": "finish", "filename": task.get_output_name(),
                               "__extra__": util.parse_task_extra(task.get_dirname())})
        if task.status == "error":
            err_path = os.path.join(task.get_dirname(), "error.txt")
            if os.path.exists(err_path):
                raise MessageException('\n'.join(open(err_path).readlines()))
            else:
                raise MessageException("Generated file fail")

    except Exception as e:
        return on_error(e)


@csrf_exempt
@require_http_methods("GET")
def download(request: HttpRequest):
    try:
        task_id = check_param("task_id", request.GET, required_type=int)
        task = Task.objects.get(task_id=int(task_id))

        if task.status != "finish":
            raise MessageException("Task doesn't finish!")

        dirname = task.get_dirname()
        name = task.get_output_name()

        file = open(os.path.join(dirname, name), 'rb')
        response = FileResponse(file)
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = 'attachment;filename="%s"' % name
        return response


    except Exception as e:
        return on_error(e)


@csrf_exempt
@require_http_methods("GET")
def config(request: HttpRequest):
    ua = user_agents.parse(get_user_agent(request))
    return on_success({
        "language": "zh" if is_cn(request) else "en",
        "speed": 20,
        "width": 540,
        "height": 960,
        "fps": 60,
        "malody_platform": "PC" if (ua.is_pc and "Mac" not in ua.get_os()) else "PE"
    })

@csrf_exempt
@require_http_methods("POST")
def report_task(request: HttpRequest):
    try:
        content = request.read()
        data = json.loads(content)
        map_name = check_param("map", data, required_type=str)
        replay_name = check_param("replay", data, required_type=str)
        bgm_name = check_param("bgm", data, required_type=str) if ("bgm" in data and data["bgm"] != "") else None
        start_time = check_param("start_time", data, required_type=int) / 1000
        end_time = check_param("end_time", data, required_type=int) / 1000
        error = check_param("error", data, required_type=str)
        version = check_param("version", data, required_type=str)
        Report(beatmap=map_name, replay=replay_name, bgm=bgm_name,
               start_time=datetime.datetime.fromtimestamp(start_time),
               end_time=datetime.datetime.fromtimestamp(end_time),
               error=error, ip=get_ip(request),
               version=version).save()
        return on_success({})
    except Exception as e:
        return on_error(e)


def check_private_call(request: HttpRequest):
    if request.POST.get('secret_key', '') != settings.SECRET_KEY:
        raise MessageException("Invalid request!")


@csrf_exempt
@require_http_methods("POST")
def private_pop_queue(request: HttpRequest):
    try:
        check_private_call(request)
        if Task.objects.filter(status="processing").count() >= settings.MAX_RUNNING_TASK:
            raise MessageException("too much working processes!")
        task = None
        for t in Task.objects.filter(status="queue").order_by("-start_time"):
            if t.activate_time is not None and (timezone.now() - t.activate_time).seconds >= 60:
                t.set_to_error("connection close")
                t.save(force_update=True)
            else:
                task = t
                break
        if task is None:
            raise MessageException("no task to run!")
        task.status = "processing"
        map = task.beatmap_file.get_path()
        replay = task.replay_file.get_path()
        if task.music_file != None:
            bgm = task.music_file.get_path()
        else:
            bgm = None
        task.save(force_update=True)
        return on_success({
            'map': map, 'replay': replay, 'bgm': bgm, 'task_id': str(task.task_id),
            'extra': task.extras, 'work_dir': task.get_dirname()
        })
    except Exception as e:
        return on_error(e)


@csrf_exempt
@require_http_methods("POST")
def private_finish_task(request: HttpRequest):
    try:
        check_private_call(request)
        task_id = check_param('task_id', request.POST)
        task = Task.objects.get(task_id=task_id)
        task.status = "finish" if task.get_output_name() is not None else "error"
        task.end_time = timezone.now()
        task.save(force_update=True)

        util.clean()

        return on_success({})
    except Exception as e:
        return on_error(e)
