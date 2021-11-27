import json
import datetime

import user_agents
from django.contrib import admin

from app.models import *

def format_time(dt: datetime.datetime):
    return (dt + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")


class ManiaFileAdmin(admin.ModelAdmin):
    list_display = ('file_id', 'file_type',
                    'file_name', 'file_save_date_time', 'ip')
    list_filter = ('file_type',)
    def file_save_date_time(self, obj):
        return format_time(obj.save_time)


class EventAdmin(admin.ModelAdmin):
    list_display = ('event_start_date_time', 'event_id', 'event_type', "event_message")
    list_filter = ('event_type',)
    def event_start_date_time(self, obj):
        return format_time(obj.time)


class TaskAdmin(admin.ModelAdmin):
    list_display = ('task_start_time', 'task_id', 'status',
                    'beatmap', 'replay', 'duration', "user_agent")
    list_filter = ('status',)


    def beatmap(self, obj):
        return "[%d] " % obj.beatmap_file.file_id + obj.beatmap_file.file_name.split(".")[-1]

    def replay(self, obj):
        return "[%d] " % obj.replay_file.file_id + obj.replay_file.file_name.split(".")[-1]

    def duration(self, obj):
        return str(obj.end_time - obj.start_time) if obj.end_time is not None else "-"

    def task_start_time(self, obj):
        return format_time(obj.start_time)

    def user_agent(self, obj):
        env = json.loads(obj.environment) if obj.environment is not None else None
        if env is None or "ua" not in env:
            return "-"
        return str(user_agents.parse(env["ua"]))


class ReportAdmin(admin.ModelAdmin):
    list_display = ('report_start_date_time', 'error', 'beatmap_type', 'replay_type',
                    'version', 'duration')
    def duration(self, obj):
        return str(obj.end_time - obj.start_time)
    def beatmap_type(self, obj):
        return obj.beatmap.split(".")[-1]
    def replay_type(self, obj):
        return obj.replay.split(".")[-1]
    def report_start_date_time(self, obj):
        return format_time(obj.start_time)

# Register your models here.
admin.site.register(ManiaFile, ManiaFileAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Report, ReportAdmin)
