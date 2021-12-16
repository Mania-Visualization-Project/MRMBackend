import json
import requests
import datetime

import user_agents
from django.contrib import admin

from app.models import *


def format_time(dt: datetime.datetime):
    return (dt + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")


ip_cache = {}
cache_validate_date = None


def ip_to_region(ip):
    global ip_cache, cache_validate_date
    now = datetime.datetime.now()
    if cache_validate_date is None or (
            now - cache_validate_date).total_seconds() >= 3600 * 24:
        ip_cache = {}
        cache_validate_date = now
    if ip in ip_cache:
        return ip_cache[ip]
    region = "-"
    try:
        data = requests.get("https://www.svlik.com/t/ipapi/ip.php?ip=" + ip).json()
        region = data['country'] + data['area']
    except:
        pass
    ip_cache[ip] = region
    return region



class ManiaFileAdmin(admin.ModelAdmin):
    list_display = ('file_id', 'file_type',
                    'file_name', 'file_save_date_time', 'region')
    list_filter = ('file_type',)

    def file_save_date_time(self, obj):
        return format_time(obj.save_time)

    def region(self, obj):
        return ip_to_region(obj.ip)


class EventAdmin(admin.ModelAdmin):
    list_display = ('event_start_date_time', 'event_id', 'event_type', "event_message")
    list_filter = ('event_type',)

    def event_start_date_time(self, obj):
        return format_time(obj.time)


class TaskAdmin(admin.ModelAdmin):
    list_display = ('task_start_date_time', 'game_mode', 'status',
                    'beatmap', 'replay', 'duration', "user_agent", "region")
    list_filter = ('status',)

    def game_mode(self, obj):
        replay_name = obj.replay_file.file_name
        if replay_name.endswith('.mr'):
            return "malody"
        if replay_name.endswith(".osr"):
            if 'Taiko' in replay_name:
                return "osu!taiko"
            if 'OsuMania' in replay_name:
                return "osu!mania"
            return "osu!"
        return "??"

    def beatmap(self, obj):
        return "[%d] " % obj.beatmap_file.file_id + obj.beatmap_file.file_name.split(".")[-1]

    def replay(self, obj):
        return "[%d] " % obj.replay_file.file_id + obj.replay_file.file_name.split(".")[-1]

    def duration(self, obj):
        return str(obj.end_time - obj.start_time) if obj.end_time is not None else "-"

    def task_start_date_time(self, obj):
        return format_time(obj.start_time)

    def user_agent(self, obj):
        env = json.loads(obj.environment) if obj.environment is not None else None
        if env is None or "ua" not in env:
            return "-"
        return str(user_agents.parse(env["ua"]))

    def region(self, obj):
        return ip_to_region(obj.ip)


class ReportAdmin(admin.ModelAdmin):
    list_display = ('report_start_date_time', 'has_error', 'beatmap_type', 'replay_type',
                    'version', 'duration', 'region')

    def duration(self, obj):
        return str(obj.end_time - obj.start_time)

    def beatmap_type(self, obj):
        return obj.beatmap.split(".")[-1]

    def replay_type(self, obj):
        return obj.replay.split(".")[-1]

    def report_start_date_time(self, obj):
        return format_time(obj.start_time)

    def has_error(self, obj):
        return obj.error is not None and obj.error != ""

    def region(self, obj):
        return ip_to_region(obj.ip)


# Register your models here.
admin.site.register(ManiaFile, ManiaFileAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Report, ReportAdmin)
