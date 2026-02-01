import asyncio
import os
import signal
import socket
import subprocess
import time
from collections.abc import AsyncIterator, Awaitable, Callable

from pantoqa_bridge.config import BRIDGE_APP_PID, IS_WINDOWS
from pantoqa_bridge.logger import logger


def create_stream_pipe() -> tuple[
  AsyncIterator[str],
  Callable[[str], Awaitable[None]],
  asyncio.Event,
]:
  queue: asyncio.Queue[str] = asyncio.Queue()
  done: asyncio.Event = asyncio.Event()

  async def push_data_to_stream(message: str) -> None:
    queue.put_nowait(message)

  async def create_stream() -> AsyncIterator[str]:
    try:
      while not done.is_set():
        yield await queue.get()
    except asyncio.CancelledError:
      pass

  return create_stream(), push_data_to_stream, done


async def stream_process(
  process: asyncio.subprocess.Process,
  on_data: Callable[[str, str], Awaitable[None]],
) -> int:
  queue: asyncio.Queue[tuple[str, str] | None] = asyncio.Queue()

  async def stream_output(stream: asyncio.StreamReader | None, label: str) -> None:
    if not stream:
      queue.put_nowait(None)
      return
    while True:
      line = await stream.readline()
      if not line:
        queue.put_nowait(None)
        break
      queue.put_nowait((label, line.decode().strip()))

  tasks: list[asyncio.Task[None]] = []
  tasks.append(asyncio.create_task(stream_output(process.stdout, "stdout")))
  tasks.append(asyncio.create_task(stream_output(process.stderr, "stderr")))

  # Stream output as it comes
  completed_streams = 0
  while completed_streams < len(tasks):
    try:
      item = await asyncio.wait_for(queue.get(), timeout=0.1)
      if item is None:
        completed_streams += 1
      else:
        stream_type, data = item
        await on_data(stream_type, data)
    except TimeoutError:
      continue

  # Wait for tasks to complete
  await asyncio.gather(*tasks)
  return await process.wait()


async def wait_for_port_to_alive(port: int, host: str = "127.0.0.1", timeout=15):
  start = time.time()
  while time.time() - start < timeout:
    try:
      with socket.create_connection((host, port), timeout=1):
        return True
    except OSError:
      await asyncio.sleep(0.25)
  raise TimeoutError("Appium did not start in time")


def watch_process_bg(
  pid: int,
  on_exit: Callable[[int], Awaitable[None] | None],
  *,
  poll_interval: float = 2.0,
) -> None:

  async def _watcher():
    try:
      while True:
        if not is_process_alive_sync(pid):
          result = on_exit(pid)
          if asyncio.iscoroutine(result):
            await result
          return

        await asyncio.sleep(poll_interval)
    except asyncio.CancelledError:
      return

  asyncio.create_task(_watcher())


def is_process_alive_sync(pid: int) -> bool:
  # TODO: Can we use psutil here?
  try:
    if IS_WINDOWS:
      # Windows: use tasklist to check if PID exists
      out = subprocess.check_output(
        ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
        stderr=subprocess.DEVNULL,
      ).decode().strip()
      # tasklist returns "INFO: No tasks are running..." if PID doesn't exist
      return str(pid) in out and "INFO:" not in out
    else:
      # Unix/Linux: use ps
      out = subprocess.check_output(["ps", "-o", "state=", "-p", str(pid)]).decode().strip()
      return "z" not in out.lower()
  except subprocess.CalledProcessError:
    return False


def kill_by_pid(pid: int):
  # TODO: Can we use psutil here?
  if IS_WINDOWS:
    subprocess.run(
      ["taskkill", "/PID", str(pid)],
      stderr=subprocess.DEVNULL,
      stdout=subprocess.DEVNULL,
    )
  else:
    os.kill(pid, signal.SIGTERM)


def force_kill_by_pid(pid: int):
  # TODO: Can we use psutil here?
  if IS_WINDOWS:
    subprocess.run(
      ["taskkill", "/F", "/PID", str(pid)],
      stderr=subprocess.DEVNULL,
      stdout=subprocess.DEVNULL,
    )
  else:
    os.kill(pid, getattr(signal, 'SIGKILL', signal.SIGTERM))


def kill_self_process():
  # DON'T WAIT HERE
  self_pid = os.getpid()
  logger.info(f"Killing self process {self_pid}...")
  kill_by_pid(self_pid)


def kill_process_gracefully(pid: int, timeout: int = 10) -> None:
  if pid <= 0:
    return

  if not is_process_alive_sync(pid):
    return

  # Step 1: graceful terminate
  logger.info(f"Terminating process {pid}...")
  if kill_by_pid(pid):
    return

  if not is_process_alive_sync(pid):
    return

  # Step 2: wait
  logger.info(f"Waiting for process {pid} to terminate...")
  start = time.time()
  while time.time() - start < timeout:
    if not is_process_alive_sync(pid):
      logger.info(f"Process {pid} terminated.")
      return
    time.sleep(0.2)

  # Step 3: force kill
  logger.info(f"Killing process {pid}...")
  force_kill_by_pid(pid)


def find_pids_by_port(port: int) -> list[int]:
  pids: list[int] = []

  try:
    if IS_WINDOWS:
      out = subprocess.check_output(
        f'netstat -ano | findstr :{port}',
        shell=True,
        text=True,
      )
      for line in out.splitlines():
        if "LISTENING" in line:
          pid_str = line.split()[-1]
          pids.append(int(pid_str))

      return pids

    out = subprocess.check_output(
      ["lsof", "-t", f"-i:{port}"],
      text=True,
    )
    for pid_str in out.split():
      pids.append(int(pid_str))
  except subprocess.CalledProcessError:
    # No process found
    pass

  return pids


def kill_process_by_port(port: int, timeout: int | None = None):
  pids = find_pids_by_port(port)
  for pid in pids:
    logger.info(f"Killing process {pid} on port {port}...")
    try:
      if timeout and timeout > 0:
        kill_process_gracefully(pid, timeout=timeout)
      else:
        kill_by_pid(pid)
    except ProcessLookupError:
      # Process already terminated
      pass


def send_outdated_signal_to_bridge_app():
  assert BRIDGE_APP_PID is not None, "BRIDGE_APP_PID is not set"
  logger.info("Sending SIGUSR1 to Bridge App for auto-upgrade...")
  if not IS_WINDOWS:
    os.kill(BRIDGE_APP_PID, getattr(signal, 'SIGUSR1', signal.SIGTERM))
    return
  WIN_UPDATE_SIGNAL_FILE = os.environ.get("WIN_UPDATE_SIGNAL_FILE")
  if not WIN_UPDATE_SIGNAL_FILE:
    os.kill(BRIDGE_APP_PID, signal.SIGTERM)
    return
  if os.path.exists(WIN_UPDATE_SIGNAL_FILE):
    os.remove(WIN_UPDATE_SIGNAL_FILE)
  open(WIN_UPDATE_SIGNAL_FILE, 'w').close()
