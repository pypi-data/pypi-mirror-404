import asyncio
from typing import Any

import aiohttp
from fastapi import APIRouter
from packaging import version as pkg_version

from pantoqa_bridge.config import APPIUM_SERVER_URL, PKG_NAME
from pantoqa_bridge.utils.pkg import get_latest_package_version, get_pkg_version, upgrade_package
from pantoqa_bridge.utils.process import kill_self_process

route = APIRouter()

_appium_utility_version = get_pkg_version("appium_utility")
_pkg_version = get_pkg_version(PKG_NAME)
_lastest_pkg_version: pkg_version.Version | None = None


async def _unset_pkg_version(timeout: int):
  global _lastest_pkg_version
  await asyncio.sleep(timeout)
  _lastest_pkg_version = None


@route.get("/health", tags=["misc"])
@route.get("/status", tags=["misc"])
async def status() -> dict[str, Any]:
  global _lastest_pkg_version
  if not _lastest_pkg_version:
    _lastest_pkg_version = get_latest_package_version(PKG_NAME)
    asyncio.create_task(_unset_pkg_version(timeout=900))  # unset after 15 minutes

  return {
    "status": "ok",
    "version": str(_pkg_version),
    "lastest_version": str(_lastest_pkg_version),
    "outdated": _lastest_pkg_version > _pkg_version,
    "appium_utility_version": str(_appium_utility_version),
  }


@route.get("/upgrade-bridge", tags=["misc"])
async def update_bridge():
  curent_pkg_version = get_pkg_version(PKG_NAME)
  latest_pkg_version = get_latest_package_version(PKG_NAME)

  if latest_pkg_version <= curent_pkg_version:
    return {
      "status": "success",
      "details": "already using the latest version.",
    }

  upgrade_package(PKG_NAME)

  async def kill_after_delay():
    await asyncio.sleep(2)
    kill_self_process()

  asyncio.create_task(kill_after_delay())

  return {
    "status": "success",
    "details": "Package upgraded successfully."
               " Please restart the application to apply the updates.",
  }


@route.get("/appium-status", tags=["misc"])
async def get_appium_status():
  async with aiohttp.ClientSession() as session:
    res = await session.get(f"{APPIUM_SERVER_URL}/status")
    res.raise_for_status()
    data = await res.json()
  return data
