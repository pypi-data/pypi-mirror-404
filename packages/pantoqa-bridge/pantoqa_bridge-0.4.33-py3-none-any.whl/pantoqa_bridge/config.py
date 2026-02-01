import os
import platform
from importlib.resources import files

from dotenv import load_dotenv

load_dotenv(
  dotenv_path=".envrc",
  verbose=True,
)

PKG_NAME = "pantoqa_bridge"


def resource_path(path: str) -> str:
  try:
    return str(files(PKG_NAME).joinpath(path))
  except Exception:
    return path


SCRCPY_SERVER_BIN = resource_path("scrcpy-server-v3.3.1")
SCRCPY_SERVER_VERSION = "3.3.1"
SCRCPY_SOCKET_PORT = 27888

IS_WINDOWS = platform.system() == "Windows"

SERVER_HOST = os.getenv("SERVER_HOST") or ("0.0.0.0" if not IS_WINDOWS else "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT") or "6565")

APPIUM_SERVER_HOST = os.getenv("APPIUM_SERVER_HOST") or SERVER_HOST
APPIUM_SERVER_PORT = int(os.getenv("APPIUM_SERVER_PORT") or "6566")
APPIUM_SERVER_URL = f"http://{APPIUM_SERVER_HOST}:{APPIUM_SERVER_PORT}"

MAESTRO_BIN = "maestro"
INACTIVITY_TIMEOUT = 5 * 60

APPIUM_BIN = os.getenv("APPIUM_BIN") or "appium"
NODE_PATH = os.getenv("NODE_PATH") or "node"
# ADBUTILS_ADB_PATH is also used by https://github.com/openatx/adbutils package
ADB_BIN = os.getenv("ADBUTILS_ADB_PATH") or "adb"

BRIDGE_APP_PID = int(os.environ["BRIDGE_APP_PID"]) if os.getenv("BRIDGE_APP_PID") else None
IS_RUNNING_IN_BRIDGE_APP = BRIDGE_APP_PID is not None
