import asyncio
import json
import sys
import tempfile
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from pantoqa_bridge.config import PKG_NAME
from pantoqa_bridge.logger import logger
from pantoqa_bridge.models.code_execute import CodeFile
from pantoqa_bridge.utils.process import (create_stream_pipe, kill_process_gracefully,
                                          stream_process)
from pantoqa_bridge.utils.service_manager import remove_all_services

route = APIRouter()


class ExecutionRequest(BaseModel):
  files: list[CodeFile]
  framework: Literal['APPIUM', 'MAESTRO']
  device_serial: str | None = None
  env_vars: dict[str, str] | None = None


class ExecutionResult(BaseModel):
  status: str
  exit_code: int | None = None
  message: str | None = None


@route.post("/execute")
async def execute(rawrequest: Request) -> StreamingResponse:
  request_json = await rawrequest.json()
  request = ExecutionRequest.model_validate(request_json)
  if not request.files:
    raise HTTPException(status_code=400, detail="At least one file is required")

  stream, push_to_stream, done = create_stream_pipe()

  async def emit(event: str, data: str) -> None:
    logger.info(f"[SSE]:{event}, data: {data}")
    await push_to_stream(_format_sse(event, data))

  async def task():
    try:
      await _execute_qacode(request, emit)
    finally:
      done.set()

  asyncio.create_task(task())
  return StreamingResponse(stream, media_type="text/event-stream")


@route.delete("/stop-test/{process_id}")
async def stop_test(process_id: str):
  kill_process_gracefully(int(process_id))


def _format_sse(event: str, data: str) -> str:
  json_dict = {
    "event": event,
    "data": data,
  }
  json_str = json.dumps(json_dict)
  return f"data: {json_str}\n\n"


async def _execute_qacode(
  request: ExecutionRequest,
  on_data: Callable[[str, str], Awaitable[None]],
):
  logger.info(f"Executing QA code with framework: {request.framework}")
  copiedfiles: list[str] = []
  with tempfile.TemporaryDirectory(prefix="pantoqa-qa-run-") as tmpdir:
    workdir = Path(tmpdir)
    for code_file in request.files:
      target = workdir / code_file.path
      target.parent.mkdir(parents=True, exist_ok=True)
      target.write_text(code_file.content, encoding="utf-8")
      copiedfiles.append(str(target))

    await on_data("status", "Starting testing...")

    process: asyncio.subprocess.Process | None = None
    try:
      remove_all_services()  # kill all the LocalBridge instance and automator connection.
      cmd = [
        sys.executable,
        "-u",  # unbuffered output
        "-m",
        PKG_NAME,
        "--skip-autoupgrade",
        "execute",
        "--framework",
        request.framework.lower(),
      ]
      if request.device_serial:
        cmd.extend(["--device", request.device_serial])
      if request.env_vars:
        env_vars_file = workdir / "env_vars.json"
        env_vars_file.write_text(json.dumps(request.env_vars), encoding="utf-8")
        cmd.extend(["--env-vars", str(env_vars_file)])
      cmd.extend(copiedfiles)
      process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=workdir,
        start_new_session=True,
        # env={**os.environ.copy(), "PYTHONUNBUFFERED": "1"},
      )
      logger.info(f"Started execution process with PID: {process.pid}")
      await on_data("pid", str(process.pid))
      await stream_process(process, on_data)
      exit_code = process.returncode
    except asyncio.CancelledError:
      if process and process.returncode is None:
        process.kill()
      await on_data("status", "Execution cancelled.")
      raise
    except Exception as e:
      if process and process.returncode is None:
        process.kill()
      exit_code = process.returncode if process else -1
      await on_data("exception", f"Execution failed: {str(e)}")
      logger.exception(f"Execution failed: {str(e)}")

    await on_data("status", f"Execution completed with exit code: {exit_code}")
    logger.info(f"Execution completed with exit code: {exit_code}")
    return exit_code
