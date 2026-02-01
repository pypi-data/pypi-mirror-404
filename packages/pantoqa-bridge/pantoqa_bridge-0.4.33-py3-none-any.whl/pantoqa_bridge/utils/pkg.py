import shutil
import subprocess
import sys
from importlib.metadata import version as importlib_version

from packaging import version as pkg_version

from pantoqa_bridge.config import IS_WINDOWS
from pantoqa_bridge.logger import logger


def get_pkg_version(pkg_name: str) -> pkg_version.Version:
  return pkg_version.parse(importlib_version(pkg_name))


def get_latest_package_version(package_name: str) -> pkg_version.Version:
  result = subprocess.check_output(
    [sys.executable, "-m", "pip", "index", "versions", package_name],
    stderr=subprocess.STDOUT,
    text=True,
  )

  if "Available versions:" not in result:
    raise ValueError(f"Could not fetch versions for package {package_name}")

  versions_str = result.split("Available versions:")[1].strip()
  latest_version = versions_str.split(",")[0].strip()
  return pkg_version.parse(latest_version)


def upgrade_package(package_name: str) -> None:
  logger.info(f"Upgrading package {package_name}...")
  try:
    if shutil.which("pipx"):
      subprocess.check_output(
        ["pipx", "upgrade", package_name],
        stderr=subprocess.STDOUT,
        text=True,
      )
    else:
      subprocess.check_output(
        [sys.executable, "-m", "pipx", "upgrade", package_name],
        stderr=subprocess.STDOUT,
        text=True,
      )
  except subprocess.CalledProcessError as e:
    if IS_WINDOWS and "PermissionError" in e.output and "WinError 32" in e.output:
      return
    logger.error(
      f"Failed to upgrade package {package_name}: {e.output}. Return Code: {e.returncode}")
    raise

  logger.info(f"Package {package_name} upgraded successfully.")
