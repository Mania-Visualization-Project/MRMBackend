# ManiaReplayMaster Backend

## API List

### Upload files
`POST` /api/upload
#### parameters (form-data)
```
{
  "type": "map", // map, bgm, replay
  "file": <data>
}
```
#### return
```
{
  "status": "OK", 
  "error_message": "", // valid when status != "OK"
  "data": {
    "file_id": "xxx"
  }
}
```

### Generate the video
`POST` /api/generate
#### parameters (body)
```
{
  "map": "map_file_id",
  "bgm": "bgm_file_id",
  "replay": "replay_file_id",
  "extra": {
    "speed": 15, "fps": 60, "malody_platform": "PE", "width": 540, "height": 960
  }
}
```
#### return
```
{
  "status": "OK", "error_message": "", "data": {"task_id": "xxx"}
}
```

### Query the progress
`GET` /api/query
#### parameters
```
{
  "task_id": "xxx"
}
```
#### return
- In queue
```
{
  "status": "OK",
  "error_message": "",
  "data": {
    "type": "queue",
    "count": 3
  }
}
```
- Processing
```
{
  "status": "OK",
  "error_message": "",
  "data": {
    "type": "processing",
    "progress": 47.55,
    "extra_": {"is_music_mismatch": false, "is_replay_mismatch": false}
  }
}
```
- Finish
```
{
  "status": "OK",
  "error_message": "",
  "data": {
    "type": "finish",
    "filename": "xxx.mp4"
    "extra_": {"is_music_mismatch": false, "is_replay_mismatch": false}
  }
}
```

### Download
`GET` api/download
#### parameters
```
{
  "task_id": "xxx"
}
```

### Terminate
`POST` api/terminate
#### parameters
```
{
  "task_id": "xxx"
}
```

## Status
|status            | ZH message                                                         |
|-------------------|--------------------------------------------------------------------|
| OK                | -                                                                  |
| error             | 内部错误：<error_message>。请将此情况反馈给我们。                                                    |
| beatmap_not_found | 上传的谱包里未找到和回放匹配的谱面。您可以手动上传指定的谱面文件。 |
| render_failed     | 视频文件生成失败！请将此情况反馈给我们。                           |
| replay_invalid    | 回放文件格式不正确！请检查您的回放文件。                           |
| beatmap_invalid   | 谱面文件格式不正确！请检查您的谱面文件。                           |
| time_exceeded     | 与服务器连接超时。请重试。                                         |