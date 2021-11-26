import json

import user_agents
from django.contrib import admin

from app.models import *


class ManiaFileAdmin(admin.ModelAdmin):
    list_display = ('file_id', 'file_type',
                    'file_name', 'save_time', 'ip')
    list_filter = ('file_type',)


class EventAdmin(admin.ModelAdmin):
    list_display = ('event_id', 'time', 'event_type', "event_message")
    list_filter = ('event_type',)


class TaskAdmin(admin.ModelAdmin):
    list_display = ('status',
                    'beatmap', 'replay',
                    'start_time', 'duration', 'error_reason', "user_agent")
    list_filter = ('status',)


    def beatmap(self, obj):
        return "[%d] " % obj.beatmap_file.file_id + obj.beatmap_file.file_name.split(".")[-1]

    def replay(self, obj):
        return "[%d] " % obj.replay_file.file_id + obj.replay_file.file_name.split(".")[-1]

    def duration(self, obj):
        return str(obj.end_time - obj.start_time) if obj.end_time is not None else "-"

    def user_agent(self, obj):
        env = json.loads(obj.environment) if obj.environment is not None else None
        if env is None or "ua" not in env:
            return "-"
        return str(user_agents.parse(env["ua"]))


class ReportAdmin(admin.ModelAdmin):
    list_display = ('report_id', 'beatmap_type',
                    'replay_type', 'version',
                    'start_time', 'duration', 'error', 'ip', 'has_error')
    def duration(self, obj):
        return str(obj.end_time - obj.start_time)
    def beatmap_type(self, obj):
        return obj.beatmap.split(".")[-1]
    def replay_type(self, obj):
        return obj.replay.split(".")[-1]
    def has_error(self, obj):
        return obj.error is not None and obj.error != ""

# Register your models here.
admin.site.register(ManiaFile, ManiaFileAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Report, ReportAdmin)
