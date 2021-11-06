# Create your views here.
import json
import os
import multiprocessing

from django.http import *
from django.utils import timezone
from django.views.decorators.csrf import *
from django.views.decorators.http import require_http_methods

from .models import ManiaFile, Task
from .worker import start_render
from MRMBackend import settings


class MessageException(Exception):
    def __init__(self, msg):
        self.msg = msg


def on_error(exception: Exception):
    if type(exception) == MessageException:
        msg = exception.msg
    else:
        import traceback
        msg = traceback.format_exc()
    return JsonResponse({"status": "error", "error_message": msg})


def on_success(obj: dict):
    obj.update({"status": "OK", "error_message": ""})
    return JsonResponse(obj)


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
                              save_time=timezone.now())
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
        print(data)
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

        task = Task(status="queue", start_time=timezone.now(), extras=extras,
                    beatmap_file=map_file, replay_file=replay_file, music_file=bgm_file)
        task.save()

        p = multiprocessing.Process(target=start_render,
                                    args=(settings.SECRET_KEY,
                                          request.get_raw_uri().replace("generate", ""),
                                          settings.MRM_PATH))
        p.start()

        return on_success({"task_id": str(task.task_id)})

    except Exception as e:
        return on_error(e)


@csrf_exempt
@require_http_methods("GET")
def query(request: HttpRequest):
    try:
        task_id = check_param("task_id", request.GET, required_type=int)
        task = Task.objects.get(task_id=int(task_id))

        # queue, processing, finish
        if task.status == "queue":
            running_count = len(list(Task.objects.filter(status="processing")))
            return on_success({"type": "queue", "count": running_count})
        if task.status == "processing":
            path = os.path.join(task.get_dirname(), "progress.txt")
            if os.path.exists(path):
                progress = float(open(path).readlines()[0].strip())
            else:
                progress = 0.0
            return on_success({"type": "processing", "progress": progress})
        if task.status == "finish":
            err_path = os.path.join(task.get_dirname(), "error.txt")
            if os.path.exists(err_path):
                raise MessageException('\n'.join(open(err_path).readlines()))
            return on_success({"type": "finish"})

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
        name = list(filter(lambda x: x.endswith("mp4"), os.listdir(dirname)))[0]

        file = open(os.path.join(dirname, name), 'rb')
        response = FileResponse(file)
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = 'attachment;filename="%s"' % name
        return response


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
        assert len(Task.objects.filter(status="processing")) < settings.MAX_RUNNING_TASK
        task = Task.objects.filter(status="queue").order_by("-start_time")[0]
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
        task.status = "finish"
        task.save(force_update=True)
        return on_success({})
    except Exception as e:
        return on_error(e)
