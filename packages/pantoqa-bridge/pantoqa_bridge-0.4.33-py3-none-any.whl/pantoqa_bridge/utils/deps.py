import os
import shutil
import subprocess
import sys
from pathlib import Path

from packaging import version as pkg_version

from pantoqa_bridge.config import (ADB_BIN, APPIUM_BIN, IS_RUNNING_IN_BRIDGE_APP, IS_WINDOWS,
                                   NODE_PATH, PKG_NAME, SCRCPY_SERVER_BIN)
from pantoqa_bridge.logger import logger
from pantoqa_bridge.utils.pkg import get_latest_package_version, get_pkg_version, upgrade_package


class Deps:

  def __init__(self):
    self._node_path: str | None = None
    self._adb_path: str | None = None
    self._appium_path: str | None = None

  def init(self):
    self.precheck_required_tools()
    self.upgrade_check()

  def upgrade_check(self):
    is_outdated, current_version, latest_version = self.is_outdated()
    if is_outdated:
      logger.info(f"[Ckeck] {PKG_NAME} is outdated: current version {current_version}, "
                  f"latest version {latest_version}.")
    else:
      logger.info(f"[Check] {PKG_NAME} is up-to-date: {current_version}")

  def auto_upgrade(self, exit_after_upgrade: bool = False):
    current_pkg_version = get_pkg_version(PKG_NAME)
    latest_pkg_version = get_latest_package_version(PKG_NAME)
    if current_pkg_version >= latest_pkg_version:
      return
    logger.info(f"[AutoUpgrade] Upgrading {PKG_NAME} from version {current_pkg_version} "
                f"to {latest_pkg_version}...")
    upgrade_package(PKG_NAME)
    logger.info(f"[AutoUpgrade] {PKG_NAME} upgraded successfully. Please restart.")
    if exit_after_upgrade:
      sys.exit(1)

  def is_outdated(self) -> tuple[bool, pkg_version.Version, pkg_version.Version]:
    current_pkg_version = get_pkg_version(PKG_NAME)
    latest_pkg_version = get_latest_package_version(PKG_NAME)
    return current_pkg_version < latest_pkg_version, current_pkg_version, latest_pkg_version

  def precheck_required_tools(self):
    self._current_package_check()
    self._node_path_check()
    self._check_adb_path()
    self._appium_path_check()
    self._uiautomator2_driver_check()
    self._check_scrcpy_server()

  def get_node(self) -> str:
    assert self._node_path is not None, "Node.js path is not set."
    return self._node_path

  def get_adb(self) -> str:
    assert self._adb_path is not None, "ADB path is not set."
    return self._adb_path

  def get_appium(self) -> str:
    assert self._appium_path is not None, "Appium path is not set."
    return self._appium_path

  def get_python(self) -> str:
    return sys.executable

  def _check_adb_path(self):
    adb_path = find_adb_path()
    if not adb_path:
      logger.warning("[Check] ADB not found. Please ensure Android SDK is installed properly.")
      raise DependencyNotInstalledError("Android SDK not found. "
                                        "Please install Android SDK "
                                        "and set ANDROID_HOME or ANDROID_SDK_ROOT "
                                        "environment variable.")
    self._adb_path = adb_path
    logger.info(f"[Check] ADB path: {adb_path}")
    if not os.environ.get("ANDROID_HOME") and not os.environ.get("ANDROID_SDK_ROOT"):
      android_path = os.path.dirname(os.path.dirname(adb_path))
      logger.info(f"[Check] Setting ANDROID_HOME to: {android_path}")
      os.environ["ANDROID_HOME"] = android_path

  def _current_package_check(self):
    current_pkg_version = get_pkg_version(PKG_NAME)
    if current_pkg_version is None:
      raise DependencyNotInstalledError(f"{PKG_NAME} is not installed properly.")
    logger.info(f"[Check] {PKG_NAME} version: {current_pkg_version}")

  def _node_path_check(self):
    node_path = shutil.which(NODE_PATH)
    if node_path is None:
      raise DependencyNotInstalledError("Node.js is not installed or not found in PATH.")
    self._node_path = node_path
    logger.info(f"[Check] Node.js found at: {self._node_path}")
    node_version = subprocess.check_output(
      [self.get_node(), "--version"],
      stderr=subprocess.STDOUT,
      text=True,
    ).strip()
    logger.info(f"[Check] Node.js version: {node_version}")

  def _appium_path_check(self):
    appium_path = shutil.which(APPIUM_BIN)
    if appium_path is None:
      raise DependencyNotInstalledError("Appium is not installed or not found in PATH.")

    if appium_path.lower().endswith("appium.cmd"):
      # On Windows, resolve the actual node_modules/appium/index.js path
      appium_path = os.path.join(
        os.path.dirname(appium_path),
        "node_modules",
        "appium",
        "index.js",
      )
      if not os.path.exists(appium_path):
        raise DependencyNotInstalledError("Appium Path not found. Please set APPIUM_BIN.")

    self._appium_path = appium_path
    logger.info(f"[Check] Appium found at: {self._appium_path}")
    appium_version = subprocess.check_output(
      [self.get_node(), self.get_appium(), "--version"],
      stderr=subprocess.STDOUT,
      text=True,
    ).strip()
    logger.info(f"[Check] Appium version: {appium_version}")

  def _uiautomator2_driver_check(self):
    uiautomator2_version = "4.2.3"
    uiautomator2_check = subprocess.check_output(
      [
        self.get_node(),
        self.get_appium(),
        "driver",
        "list",
        "--installed",
        "--json",
      ],
      stderr=subprocess.STDOUT,
      text=True,
    )
    if "uiautomator2" in uiautomator2_check:
      logger.info("[Check] Appium uiautomator2 driver is installed.")
      return

    if IS_RUNNING_IN_BRIDGE_APP:
      raise DependencyNotInstalledError(
        "[Check] Appium uiautomator2 driver is not installed in Bridge App.", )

    logger.info("[Check] Appium uiautomator2 driver is not installed. Installing...")
    try:
      subprocess.check_output(
        [
          self.get_node(),
          self.get_appium(),
          "driver",
          "install",
          f"uiautomator2@{uiautomator2_version}",
        ],
        stderr=subprocess.STDOUT,
        text=True,
      )
      logger.info("[Check] Appium uiautomator2 driver installed successfully.")
    except subprocess.CalledProcessError as e:
      raise DependencyNotInstalledError(
        f"Failed to install Appium uiautomator2 driver: {e.output}") from e

  def _check_scrcpy_server(self):
    if not os.path.exists(SCRCPY_SERVER_BIN):
      raise DependencyNotInstalledError(
        "[Check] scrcpy server binary not found. Screen mirroring may not work properly.")

    logger.info(f"[Check] scrcpy server binary found at: {SCRCPY_SERVER_BIN}")


class DependencyNotInstalledError(Exception):
  pass


def find_android_home() -> str | None:
  """
  Find ANDROID_HOME path by checking:
  1. adb location (SDK root is parent of platform-tools)
  2. Common SDK installation paths
  Returns the path as a string, or None if not found.
  """

  if os.environ.get("ANDROID_HOME"):
    return os.environ["ANDROID_HOME"]

  if os.environ.get("ANDROID_SDK_ROOT"):
    return os.environ["ANDROID_SDK_ROOT"]

  # Try to find SDK root from adb location
  adb_path = shutil.which("adb")
  if adb_path:
    # adb is in <SDK>/platform-tools/adb, so SDK root is grandparent
    sdk_root = Path(adb_path).resolve().parent.parent
    if sdk_root.exists():
      return str(sdk_root)

  # Try common SDK locations
  home = Path.home()
  if IS_WINDOWS:
    common_paths = [
      Path(f"{home}/AppData/Local/Android/Sdk"),
      Path("C:/Android/Sdk"),
      Path("C:/Android/android-sdk"),
    ]
  else:  # Mac/Linux
    common_paths = [
      Path(f"{home}/Library/Android/sdk"),
      Path(f"{home}/Android/Sdk"),
      Path("/usr/local/android-sdk"),
    ]

  for sdk_path in common_paths:
    if sdk_path.exists() and (sdk_path / "platform-tools").exists():
      return str(sdk_path)

  return None


def find_adb_path() -> str | None:
  if shutil.which(ADB_BIN):
    return shutil.which(ADB_BIN)

  android_home = find_android_home()
  if not android_home:
    return None
  adb_path = os.path.join(android_home, "platform-tools", "adb")
  if os.path.exists(adb_path):
    return adb_path
  return None


deps = Deps()
