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
    "progress": 47.55
  }
}
```
- Finish
```
{
  "status": "OK",
  "error_message": "",
  "data": {
    "type": "finish"
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