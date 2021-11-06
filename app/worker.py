import json
import os
import requests
import shutil
import subprocess

CONFIG = """
# Falling down speed, in pixel / frame
speed: {speed}

# FPS: frame / second
framePerSecond: {fps}

# Only valid when using Malody. true: PE, false: PC
malodyPE: {malodyPE}

# UI settings
width: {w}
height: {h}
actionHeight: 7
blockHeight: 40
stroke: 3

# Judgement colors
judgementColor:
  - FFFFFF
  - FFD237
  - 79D020
  - 1E68C5
  - E1349B
longNoteColor: '646464'
missColor: FF0000

# Advanced
outputDir: '{output}'
codec: libx264
debug: true
server: true
"""


def start_render(secret, end_point, mrm_path):
    print(secret, end_point, mrm_path)
    while True:
        task_obj = requests.post(end_point + "pop_queue", data={
            'secret_key': secret
        }).json()
        print("task obj", task_obj)
        if task_obj['status'] != 'OK':
            print('Not render!')
            break

        if task_obj['bgm'] is not None:
            shutil.copy(task_obj['bgm'], os.path.dirname(task_obj['map']))

        extra = json.loads(task_obj['extra'])
        work_dir = task_obj['work_dir']

        config_text = CONFIG.format(
            speed=extra.get("speed", 15),
            fps=extra.get("fps", 60),
            malodyPE="true" if extra.get("malody_platform", "PE") == "PE" else "false",
            w=extra.get("width", 540),
            h=extra.get("height", 960),
            output=work_dir
        )
        config_path = os.path.join(work_dir, "config.txt")
        with open(config_path, "w") as f:
            f.write(config_text)

        subprocess.call([
            "java", "-jar",
            str(mrm_path),
            str(task_obj['map']),
            str(task_obj['replay']),
            config_path
        ])

        print(requests.post(end_point + "finish_task", data={
            'secret_key': secret,
            'task_id': task_obj['task_id']
        }).json())
