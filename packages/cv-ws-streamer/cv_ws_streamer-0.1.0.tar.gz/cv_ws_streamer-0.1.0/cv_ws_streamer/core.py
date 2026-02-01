import asyncio
import json
from typing import Optional, Callable, Dict, Any, Awaitable
from fastapi import WebSocket, WebSocketDisconnect
import numpy as np
import cv2

class Streamer:
    """
    High-performance WebSocket streamer for OpenCV frames using custom binary protocol.
    Protocol:
    - 0x01: Video Frame (JPEG bytes)
    - 0x02: JSON Metadata (UTF-8 bytes)
    """
    
    VIDEO_HEADER = b'\x01'
    JSON_HEADER = b'\x02'

    def __init__(self, jpeg_quality: int = 70):
        self.active_connection: Optional[WebSocket] = None
        self.jpeg_quality = jpeg_quality
        self.on_message_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None
        
    async def connect(self, websocket: WebSocket):
        """Accepts the websocket connection and manages the receiving loop."""
        await websocket.accept()
        self.active_connection = websocket
        
        try:
            while True:
                # Wait for messages from the client (e.g., clicks)
                data = await websocket.receive_text()
                try:
                    event = json.loads(data)
                    if self.on_message_callback:
                        await self.on_message_callback(event)
                except json.JSONDecodeError:
                    print(f"Received invalid JSON: {data}")
        except WebSocketDisconnect:
            print("Client disconnected")
            self.active_connection = None
        except Exception as e:
            print(f"WebSocket error: {e}")
            self.active_connection = None

    def on_message(self, func: Callable[[Dict[str, Any]], Awaitable[None]]):
        """Decorator to register a callback for client messages."""
        self.on_message_callback = func
        return func

    async def send_frame(self, frame: np.ndarray):
        """Encodes and sends a frame."""
        if not self.active_connection:
            return

        # Encode frame
        success, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality])
        if not success:
            return

        # Prepare payload: Header + JPEG Bytes
        payload = self.VIDEO_HEADER + buffer.tobytes()

        try:
            await self.active_connection.send_bytes(payload)
        except Exception:
            pass

    async def send_data(self, data: Dict[str, Any]):
        """Sends JSON metadata to the client."""
        if not self.active_connection:
            return
            
        json_bytes = json.dumps(data).encode('utf-8')
        payload = self.JSON_HEADER + json_bytes
        
        try:
            await self.active_connection.send_bytes(payload)
        except Exception:
            pass
