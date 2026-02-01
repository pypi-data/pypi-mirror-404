import base64
import re
from io import BytesIO

import uiautomator2 as u2  # type: ignore
from adbutils import adb  # type: ignore

from pantoqa_bridge.logger import logger


class LocalBridgeService():

  def __init__(self, device_serial: str):
    self.uiautomator: u2.Device | None = None
    self.adb = adb.device(device_serial)
    self._device_resolution: dict | None = None

  def __enter__(self):
    # self.uiautomator.start_uiautomator()
    return self

  def __exit__(self, exc_type, exc, tb):
    self.stop()
    return False

  def stop(self):
    if self.uiautomator:
      self.uiautomator.stop_uiautomator()
      self.uiautomator = None
    ...

  def take_screenshot(self) -> str:
    image = self.adb.screenshot()
    buf = BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")

  def click(self, x: int, y: int):
    self.adb.click(x, y)

  def long_click(self, x: int, y: int):
    duration = 100
    self.adb.swipe(x, y, x, y, duration=duration)

  def get_os_version(self) -> str:
    version = self.adb.shell("getprop ro.build.version.release")
    return f"Android {version.strip()}" if version else "unknown"

  def get_device_model(self) -> str:
    result = self.adb.shell("getprop ro.product.model")
    return result.strip()

  def device_resolution(self) -> dict:
    if self._device_resolution:
      return self._device_resolution
    txt_result = self.adb.shell("wm size")

    txt_result = txt_result.replace("Physical size:", "").strip()

    match = re.search(r'(\d+)\s*x\s*(\d+)', txt_result)
    if not match:
      raise ValueError(f"Could not parse resolution from: {txt_result!r}")

    width, height = map(int, match.groups())
    logger.debug(f"Device resolution: {width}x{height}")
    self._device_resolution = {"width": width, "height": height}
    return self._device_resolution

  def get_ui_dump(self) -> str:
    try:
      xml = self.adb.dump_hierarchy()
      return xml
    except Exception:
      pass

    if not self.uiautomator:
      self.uiautomator = u2.connect_adb(self.adb.serial)

    xml = self.uiautomator.dump_hierarchy()
    return xml

  def get_current_app_activity(self) -> str | None:
    result = self.adb.shell("dumpsys window")
    for line in result.splitlines():
      if "mCurrentFocus" in line:
        # Equivalent of grep -Eo 'u0\s+\S+/\S+'
        match = re.search(r'u0\s+\S+/\S+', line)
        if match:
          activity = match.group(0).split()[1]  # awk '{print $2}'
          # Equivalent of sed 's/[}:]*$//'
          return re.sub(r'[}:]*$', '', activity)
    return None

  def get_main_activity(self, package_name: str) -> str | None:
    result = self.adb.shell(f"cmd package resolve-activity --brief {package_name}")

    for line in result.splitlines():
      if line.startswith(package_name + "/"):
        return line.replace(package_name + "/", "", 1)

    return None

  def get_all_packages(self) -> list[str]:
    packages = self.adb.list_packages()
    return packages

  def open_app(self, package_name: str, activity_name: str = ".MainActivity"):
    self.adb.app_start(package_name, activity_name)

  def close_keyboard(self):
    self.go_back()

  def press_enter(self):
    self.adb.shell("input keyevent 66")

  def go_back(self):
    self.adb.shell("input keyevent 4")

  def is_keyboard_open(self) -> bool:
    result = self.adb.shell("dumpsys input_method")
    return "mInputShown=true" in result

  def goto_home(self):
    self.adb.shell("input keyevent 3")

  def clear_all_inputs(self):
    self.adb.shell("input keycombination 113 29")  # select all (ctrl + a)
    self.backspace()

  def backspace(self):
    self.adb.shell("input keyevent 67")

  def input_text(self, text: str):
    text = _adb_encode(text)
    self.adb.shell(f'input text "{text}"')

  def swipe(self, x1: int, y1: int, x2: int, y2: int):
    self.adb.swipe(x1, y1, x2, y2)

  def long_press(self, x: int, y: int):
    duration = 100
    self.adb.swipe(x, y, x, y, duration=duration)

  def get_oem_name(self) -> str:
    result = self.adb.shell("getprop ro.product.manufacturer")
    return result.strip()

  def get_device_name(self) -> str:
    result = self.adb.shell("getprop ro.product.model")
    return result.strip()

  def get_os_build_version(self) -> str:
    result = self.adb.shell("getprop ro.build.display.id")
    return result.strip()


def _adb_encode(text: str) -> str:
  escape_map = {
    '%': r'\%',
    ' ': '%s',
    "'": r"\'",
    '"': r'\"',
    '&': r'\&',
    '(': r'\(',
    ')': r'\)',
    ';': r'\;',
    '<': r'\<',
    '>': r'\>',
    '\\': r'\\',
  }
  encoded = ""
  for ch in text:
    encoded += escape_map.get(ch, ch)
  return encoded
