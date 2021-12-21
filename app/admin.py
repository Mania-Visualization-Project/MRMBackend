import json
import requests
import datetime

import user_agents
from django.contrib import admin
from django.utils.html import format_html

from app.models import *
from app import util


def format_time(dt: datetime.datetime):
    return (dt + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")


ip_cache = {}
cache_validate_date = None


def ip_to_region(ip):
    ip_region = IPRegion.objects.filter(ip=ip).first()
    if ip_region is None:
        try:
            data = requests.get("https://www.svlik.com/t/ipapi/ip.php?ip=" + ip).json()
            print(data)
            ip_region = IPRegion(ip=ip, country=data['country'], area=data['area'])
            ip_region.save()
        except:
            pass
    if ip_region is None:
        return "-"
    else:
        return ip_region.get_region()


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


class IPRegionAdmin(admin.ModelAdmin):
    list_display = ('ip', 'country', 'area', 'online_pv', 'offline_pv', 'total_pv')

    def online_pv_int(self, ip):
        return util.get_from_cache('online_pv', 10, default_func=lambda: list(map(
            lambda x: x['ip'],
            Task.objects.all().values('ip')
        ))).count(ip)

    def online_pv(self, obj):
        online_pv_list = self.online_pv_int(obj.ip)
        return format_html('<a href="%s">%d</a>' % ('/mania/admin/app/task/?q=' + obj.ip, online_pv_list))

    online_pv.allow_tags = True

    def offline_pv_int(self, ip):
        return util.get_from_cache('offline_pv', 10, default_func=lambda: list(map(
            lambda x: x['ip'],
            Report.objects.all().values('ip')
        ))).count(ip)

    def offline_pv(self, obj):
        online_pv_list = self.offline_pv_int(obj.ip)
        return format_html('<a href="%s">%d</a>' % ('/mania/admin/app/report/?q=' + obj.ip, online_pv_list))

    def total_pv(self, obj):
        return self.online_pv_int(obj.ip) + self.offline_pv_int(obj.ip)


class TaskAdmin(admin.ModelAdmin):
    list_display = ('task_start_date_time', 'game_mode_display', 'status',
                    'beatmap', 'replay', 'duration', "user_agent", "region")
    list_filter = ('status',)
    search_fields = ('ip',)

    def game_mode_display(self, obj):
        if obj.game_mode is None:
            replay_name = obj.replay_file.file_name
            return util.parse_game_mode_from_replay(replay_name)
        else:
            return obj.game_mode

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
    list_display = (
    'report_start_date_time', 'has_error', 'game_mode_display', 'beatmap_type', 'replay_type',
    'version', 'duration', 'region')
    search_fields = ('ip',)

    def game_mode_display(self, obj):
        if obj.game_mode is None:
            replay_name = obj.replay
            return util.parse_game_mode_from_replay(replay_name)
        else:
            return obj.game_mode

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
admin.site.register(IPRegion, IPRegionAdmin)
