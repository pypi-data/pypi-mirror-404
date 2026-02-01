# cv-ws-streamer

A high-performance Python library for streaming frames (OpenCV/NumPy) to a React client via Binary WebSockets.

## Features
- 🚀 **Binary Protocol**: Low overhead MJPEG streaming.
- **Two-way Communication**: Handle clicks and events from the frontend.
- **FastAPI Integration**: Easy to drop into existing FastAPI apps.

## Installation

```bash
pip install cv-ws-streamer
```

## Usage

```python
from fastapi import FastAPI, WebSocket
from cv_ws_streamer.core import Streamer
import cv2

app = FastAPI()
streamer = Streamer(jpeg_quality=70)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await streamer.connect(websocket)

# In your video loop:
# await streamer.send_frame(frame)
```
