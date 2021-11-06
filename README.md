# ManiaReplayMaster Backend

## API List

### Upload files
`POST` /api/upload
#### parameters (form-data)
```json
{
  "type": "map", // map, bgm, replay
  "file": <data>
}
```
#### return
```json
{
  "status": "OK", 
  "error_message": "", // valid when status != "OK"
  "file_id": "xxx"
}
```

### Generate the video
`POST` /api/generate
#### parameters (body)
```json
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
```json
{
  "status": "OK", "error_message": "", "task_id": "xxx"
}
```

### Query the progress
`GET` /api/query
#### parameters
```json
{
  "task_id": "xxx"
}
```
#### return
- In queue
```json
{
  "status": "OK",
  "error_message": "",
  "type": "queue",
  "count": 3
}
```
- Processing
```json
{
  "status": "OK",
  "error_message": "",
  "type": "processing",
  "progress": 47.55
}
```
- Finish
```json
{
  "status": "OK",
  "error_message": "",
  "type": "finish"
}
```

### Download
`GET` api/download
#### parameters
```json
{
  "task_id": "xxx"
}
```