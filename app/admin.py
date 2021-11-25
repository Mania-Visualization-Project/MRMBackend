import json

import user_agents
from django.contrib import admin

from app.models import *


class ManiaFileAdmin(admin.ModelAdmin):
    list_display = ('file_id', 'file_type',
                    'file_name', 'save_time', 'ip')


class EventAdmin(admin.ModelAdmin):
    list_display = ('event_id', 'time', 'event_type', "event_message")


class TaskAdmin(admin.ModelAdmin):
    list_display = ('task_id', 'status',
                    'beatmap', 'replay', 'music',
                    'start_time', 'duration', 'error_reason', 'ip', "user_agent")

    def beatmap(self, obj):
        return "%d" % obj.beatmap_file.file_id

    def replay(self, obj):
        return "%d" % obj.replay_file.file_id

    def music(self, obj):
        return "null" if obj.music_file is None else (
                "%d" % obj.music_file.file_id
        )

    def duration(self, obj):
        return str(obj.end_time - obj.start_time) if obj.end_time is not None else "-"

    def user_agent(self, obj):
        env = json.loads(obj.environment) if obj.environment is not None else None
        if env is None or "ua" not in env:
            return "-"
        return str(user_agents.parse(env["ua"]))


# Register your models here.
admin.site.register(ManiaFile, ManiaFileAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(Event, EventAdmin)
