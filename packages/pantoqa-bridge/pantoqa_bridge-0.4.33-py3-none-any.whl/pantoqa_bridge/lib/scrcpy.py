import asyncio
import signal
import socket
from asyncio.subprocess import Process
from collections.abc import Awaitable, Callable

from pantoqa_bridge.config import SCRCPY_SERVER_BIN, SCRCPY_SERVER_VERSION, SCRCPY_SOCKET_PORT
from pantoqa_bridge.lib.adb import ADB
from pantoqa_bridge.logger import logger


class InvalidDummyByte(Exception):
  ...


class ScrcpyPyClient:

  def __init__(
    self,
    on_frame_update: Callable[[bytes], Awaitable[None]],
    max_size: int | None = None,
    server_version: str = SCRCPY_SERVER_VERSION,
    sever_port: int = SCRCPY_SOCKET_PORT,
    server_bin: str = SCRCPY_SERVER_BIN,
    adb: ADB | None = None,
    device_serial: str | None = None,
  ):
    self.on_frame = on_frame_update
    self.device_serial = device_serial
    self.adb = adb or ADB(device_serial=self.device_serial)
    self.server_bin = server_bin
    self.socket_port = sever_port
    self.server_version = server_version
    self.max_size = max_size or 720
    self._is_stopping = asyncio.Event()
    self._remote_tmp_path = f"/data/local/tmp/scrcpy-server{self.server_version}"
    self._scrcpy_process: Process | None = None

  async def push_server(self):
    await self.adb.push(self.server_bin, self._remote_tmp_path)

  async def start_server(self):
    cmd = [
      "shell",
      f"CLASSPATH={self._remote_tmp_path}",
      "app_process",
      "/",
      "com.genymobile.scrcpy.Server",
      self.server_version,
      "control=false",
      "audio=false",
      "tunnel_forward=true",
      f"max_size={self.max_size}",
    ]
    process = await self.adb.exec_p(cmd)
    self._scrcpy_process = process
    assert process.stdout, "Scrcpy process stdout is None."
    data = await process.stdout.readline()  # some delay until server starts
    logger.info(f"[Scrcpy]: {data!r}")
    logger.info("Scrcpy server started.")

  async def forward_video_socket(self):
    cmd = ["forward", f"tcp:{self.socket_port}", "localabstract:scrcpy"]
    await self.adb.exec(cmd)

  async def read_video_socket(self, connect_timeout: int = 30):

    async def connect() -> socket.socket:
      logger.info("Trying to connect to video socket...")
      sock = socket.create_connection(("127.0.0.1", self.socket_port), timeout=5)
      sock.setblocking(False)
      loop = asyncio.get_running_loop()
      DUMMY_FIELD_LENGTH = 1
      dummy_byte = await loop.sock_recv(sock, DUMMY_FIELD_LENGTH)
      if not len(dummy_byte) or dummy_byte != b"\x00":
        logger.info(f"Received invalid dummy byte: {dummy_byte!r}")
        sock.close()
        raise InvalidDummyByte("invalid_dummy_byte")

      return sock

    async def connect_with_retries(connect_timeout: int = 30) -> socket.socket:
      start_time = asyncio.get_running_loop().time()
      while True:
        logger.info("Attempting to connect to scrcpy video socket...")
        try:
          sock = await connect()
          return sock
        except InvalidDummyByte as e:
          if asyncio.get_running_loop().time() - start_time > connect_timeout:
            raise TimeoutError("Timeout connecting to scrcpy video socket.")
          logger.info(f"Connection to video socket failed: {e}. Retrying...")
          await asyncio.sleep(1)

    sock = await connect_with_retries(connect_timeout)
    logger.info("Connected to video socket. Streaming video data...")

    loop = asyncio.get_running_loop()
    try:
      while not self._is_stopping.is_set():
        try:
          raw_data = await loop.sock_recv(sock, 0x10000)
          if not raw_data:
            logger.info("No more data from video stream. Exiting...")
            break
          await self.on_frame(raw_data)
        except asyncio.CancelledError:
          logger.info("Video socket read task cancelled.")
          break
        except Exception as e:
          logger.info(f"Error reading video stream: {e}")
          break
    finally:
      logger.info("Closing video socket...")
      try:
        sock.close()
      except Exception:
        pass

  async def stop(self):
    self._is_stopping.set()
    cmd = ["forward", "--remove", f"tcp:{self.socket_port}"]
    await self.adb.exec(cmd, skip_check=True)
    logger.info("Stopped scrcpy client.")
    try:
      if self._scrcpy_process:
        logger.info("Terminating scrcpy server process...")
        self._scrcpy_process.send_signal(signal.SIGTERM)
        await self._scrcpy_process.wait()
    except ProcessLookupError:
      pass
