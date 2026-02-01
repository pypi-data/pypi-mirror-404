import threading
import time

import adbutils  # type: ignore

from pantoqa_bridge.config import INACTIVITY_TIMEOUT
from pantoqa_bridge.logger import logger
from pantoqa_bridge.models.misc import Action
from pantoqa_bridge.service.uiautomator_action import LocalBridgeService


class ServiceManager:

  def __init__(self, device_serial: str):
    self.device_serial = device_serial
    self.srv = LocalBridgeService(device_serial)
    self.last_used = time.time()
    self._lock = threading.Lock()
    self._closed = False

    self._cleanup_thread = threading.Thread(target=self._auto_cleanup, daemon=True)
    self._cleanup_thread.start()

  def touch(self):
    with self._lock:
      self.last_used = time.time()

  def process(self, action: Action):
    self.touch()
    return _process_action(self.srv, action)

  def _auto_cleanup(self):
    while True:
      time.sleep(30)
      with self._lock:
        if self._closed:
          return

        if time.time() - self.last_used > INACTIVITY_TIMEOUT:
          self.close()
          return

  def close(self):
    if self._closed:
      return
    self._closed = True
    try:
      self.srv.stop()
    finally:
      remove_service(self.device_serial)


_services: dict[str, ServiceManager] = {}
_services_lock = threading.Lock()


def get_service(device_serial: str | None = None) -> ServiceManager:
  adb = adbutils.AdbClient()
  devices = adb.device_list()

  if not device_serial:
    device_serial = devices[0].serial

  with _services_lock:
    if device_serial not in _services:
      _services[device_serial] = ServiceManager(device_serial)
    return _services[device_serial]


def remove_service(device_serial: str):
  with _services_lock:
    _services.pop(device_serial, None)


def remove_all_services():
  with _services_lock:
    services = list(_services.values())
    _services.clear()

  for srv_mgr in services:
    try:
      srv_mgr.close()
    except Exception as e:
      logger.error(f"Error while closing service managers:{e}")


def _process_action(srv: LocalBridgeService, action: Action):
  action_type = action.action_type
  if action_type == "screenshot":
    return srv.take_screenshot()
  if action_type == "click":
    params = action.params
    assert params, "params is not present."
    srv.click(params['x'], params['y'])
    return
  if action_type == "long_click":
    params = action.params
    assert params, "params is not present."
    srv.long_click(params['x'], params['y'])
    return
  if action_type == "get_os_version":
    return srv.get_os_version()
  if action_type == "get_device_model":
    return srv.get_device_model()
  if action_type == "get_device_resolution":
    return srv.device_resolution()
  if action_type == "get_ui_dump":
    return srv.get_ui_dump()
  if action_type == "get_current_app_activity":
    return srv.get_current_app_activity()
  if action_type == "get_main_activity":
    params = action.params
    assert params, "params is not present."
    return srv.get_main_activity(params['package_name'])
  if action_type == "get_all_packages":
    return srv.get_all_packages()
  if action_type == "open_app":
    params = action.params
    assert params, "params is not present."
    srv.open_app(params['package_name'], params['activity_name'])
    return
  if action_type == "close_keyboard":
    srv.close_keyboard()
    return
  if action_type == "press_enter":
    srv.press_enter()
    return
  if action_type == "go_back":
    srv.go_back()
    return
  if action_type == "is_keyboard_open":
    return srv.is_keyboard_open()
  if action_type == "goto_home":
    srv.goto_home()
    return
  if action_type == "clear_all_inputs":
    srv.clear_all_inputs()
    return
  if action_type == "backspace":
    srv.backspace()
    return
  if action_type == "input_text":
    params = action.params
    assert params, "params is not present."
    srv.input_text(params['text'])
    return
  if action_type == "swipe":
    params = action.params
    assert params, "params is not present."
    srv.swipe(params['x1'], params['y1'], params['x2'], params['y2'])
    return
  if action_type == "long_press":
    params = action.params
    assert params, "params is not present."
    srv.long_press(params['x'], params['y'])
    return
  if action_type == "get_oem_name":
    return srv.get_oem_name()
  if action_type == "get_device_name":
    return srv.get_device_name()
  if action_type == "get_os_build_version":
    return srv.get_os_build_version()
  if action_type == "stop":
    return srv.stop()

  raise ValueError(f"Unsupported action type: {action_type}")
