import os
import subprocess
import threading
import time
from collections.abc import Callable

from pantoqa_bridge.config import APPIUM_SERVER_HOST, APPIUM_SERVER_PORT
from pantoqa_bridge.logger import logger
from pantoqa_bridge.utils.deps import deps
from pantoqa_bridge.utils.process import kill_process_by_port


def start_appium_process_in_bg(on_exit: Callable[[int, int], None]):

  def start():
    cmd = [
      deps.get_node(),
      deps.get_appium(),
      "--session-override",
      "--port",
      str(APPIUM_SERVER_PORT),
      "--address",
      APPIUM_SERVER_HOST,
    ]
    logger.info(f"Starting Appium at http://{APPIUM_SERVER_HOST}:{APPIUM_SERVER_PORT}")

    proc = subprocess.Popen(
      cmd,
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
      start_new_session=True,
      shell=False,
      env=os.environ.copy(),
    )
    logger.info("Appium process started with PID: %d", proc.pid)
    return proc

  def start_in_loop():
    max_retries = 2
    proc: subprocess.Popen[bytes] | None = None
    while max_retries > 0:
      max_retries -= 1
      proc = start()
      proc.wait()
      if proc.returncode != 1:
        break
      logger.error("Appium process exited with errors. Return code: %d", proc.returncode)
      kill_process_by_port(APPIUM_SERVER_PORT, timeout=5)
      time.sleep(1)
    if proc:
      on_exit(proc.pid, proc.returncode)
    else:
      on_exit(-1, -1)

  try:
    kill_process_by_port(APPIUM_SERVER_PORT, timeout=5)
  except Exception:
    pass
  thread = threading.Thread(target=start_in_loop, daemon=True)
  thread.start()
  logger.info("Starting Appium process in background.")
