import asyncio
import subprocess
from asyncio.subprocess import Process
from typing import Literal, overload

from pantoqa_bridge.logger import logger
from pantoqa_bridge.utils.deps import deps


class ADB:

  def __init__(
    self,
    adb: str | None = None,
    device_serial: str | None = None,
  ):
    self.adb = adb or deps.get_adb()
    self.device_serial = device_serial

  async def device_list(self) -> list[str]:
    cmd = ["devices"]
    res = await self._run_adb_cmd(cmd)
    lines = res.stdout.decode().splitlines()
    devices = []
    for line in lines[1:]:
      if line.strip():
        device_id = line.split("\t")[0]
        devices.append(device_id)
    return devices

  async def push(
    self,
    local_path: str,
    remote_path: str,
  ) -> subprocess.CompletedProcess:
    cmd = ["push", local_path, remote_path]
    res = await self._run_adb_cmd(cmd)
    return res

  async def shell(self, command: str) -> subprocess.CompletedProcess:
    cmd = ["shell", command]
    res = await self._run_adb_cmd(cmd)
    return res

  async def exec(
    self,
    command: list[str],
    skip_check: bool = False,
  ) -> subprocess.CompletedProcess:
    return await self._run_adb_cmd(
      command,
      skip_check=skip_check,
    )

  async def exec_p(
    self,
    command: list[str],
  ) -> Process:
    return await self._run_adb_cmd(command, return_process=True)

  @overload
  async def _run_adb_cmd(
    self,
    cmd: list[str],
    *,
    return_process: Literal[True],
    skip_check: bool = False,
  ) -> Process:
    ...

  @overload
  async def _run_adb_cmd(
    self,
    cmd: list[str],
    *,
    return_process: Literal[False] = False,
    skip_check: bool = False,
  ) -> subprocess.CompletedProcess:
    ...

  async def _run_adb_cmd(
    self,
    cmd: list[str],
    *,
    return_process: bool = False,
    skip_check=False,
  ) -> subprocess.CompletedProcess | Process:
    if self.device_serial:
      cmds = [self.adb, "-s", self.device_serial] + cmd
    else:
      cmds = [self.adb] + cmd

    logger.info(f"Executing ADB command: {' '.join(cmds)}")

    process = await asyncio.create_subprocess_exec(
      *cmds,
      stdout=asyncio.subprocess.PIPE,
      stderr=asyncio.subprocess.PIPE,
    )
    if return_process:
      return process

    stdout, stderr = await process.communicate()

    if not skip_check and process.returncode != 0:
      raise subprocess.CalledProcessError(
        process.returncode or -1,
        cmds,
        output=stdout,
        stderr=stderr,
      )

    return subprocess.CompletedProcess(cmds, process.returncode or 0, stdout, stderr)
