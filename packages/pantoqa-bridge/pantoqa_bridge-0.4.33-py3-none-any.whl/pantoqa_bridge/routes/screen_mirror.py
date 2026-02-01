import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from pantoqa_bridge.lib.scrcpy import ScrcpyPyClient
from pantoqa_bridge.logger import logger

route = APIRouter()


@route.websocket("/ws/mirror")
async def ws_endpoint(ws: WebSocket):
  await ws.accept()
  streaming: ScreenMirrorOverWS | None = None
  try:
    params = ws.query_params
    max_size = int(params["max_size"]) if params.get("max_size") else None
    device_serial = params.get("device_serial") if params.get("device_serial") else None
    streaming = ScreenMirrorOverWS(ws, max_size, device_serial)
    await streaming.stream()  # blocking call
  except WebSocketDisconnect:
    logger.warning("WebSocket disconnected.")
  except Exception as e:
    logger.exception(f"Error in WebSocket endpoint: {e}")
  finally:
    if streaming:
      await streaming.teardown()


class ScreenMirrorOverWS:

  def __init__(self, ws: WebSocket, max_size: int | None = None, device_serial: str | None = None):
    self.ws = ws
    self.scrcpy: ScrcpyPyClient | None = None
    self._is_streaming = False
    self._socket_read_task: asyncio.Task[None] | None = None
    self.max_size = max_size
    self.device_serial = device_serial

  async def stream(self):
    if self._is_streaming:
      return
    self._is_streaming = True
    self.scrcpy = ScrcpyPyClient(on_frame_update=self.on_frame_update,
                                 max_size=self.max_size,
                                 device_serial=self.device_serial)
    await self.scrcpy.push_server()
    await self.scrcpy.forward_video_socket()
    await self.scrcpy.start_server()
    self._socket_read_task = asyncio.create_task(self.scrcpy.read_video_socket())
    logger.info("Started streaming screen over WebSocket.")
    await self._socket_read_task  # Blocking call to keep streaming

  async def on_frame_update(self, frame: bytes):
    await self.ws.send_bytes(frame)

  async def teardown(self):
    self._is_streaming = False

    if self.scrcpy:
      logger.info("[teardown]Stopping scrcpy client...")
      try:
        await self.scrcpy.stop()
      finally:
        self.scrcpy = None

    if self._socket_read_task and not self._socket_read_task.done():
      logger.info("[teardown]Cancelling socket read task...")
      try:
        self._socket_read_task.cancel()
      finally:
        self._socket_read_task = None

    logger.info("[teardown]Teardown complete.")
