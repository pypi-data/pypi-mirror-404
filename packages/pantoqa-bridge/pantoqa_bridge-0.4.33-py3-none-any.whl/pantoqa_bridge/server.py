from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pantoqa_bridge.config import (APPIUM_SERVER_HOST, APPIUM_SERVER_PORT,
                                   IS_RUNNING_IN_BRIDGE_APP, SERVER_HOST, SERVER_PORT)
from pantoqa_bridge.logger import logger
from pantoqa_bridge.routes.action import router as action_router
from pantoqa_bridge.routes.adb import router as adb_router
from pantoqa_bridge.routes.executor import route as executor_route
from pantoqa_bridge.routes.misc import route as misc_route
from pantoqa_bridge.routes.screen_mirror import route as screen_mirror_route
from pantoqa_bridge.utils.appium import start_appium_process_in_bg
from pantoqa_bridge.utils.deps import DependencyNotInstalledError, deps
from pantoqa_bridge.utils.process import (kill_process_by_port, kill_self_process,
                                          wait_for_port_to_alive)


def create_app() -> FastAPI:

  def on_exit(pid: int, returncode: int) -> None:
    if returncode == 0:
      logger.info(f"Appium process exited normally PID={pid}.")
      return

    logger.info(f"Appium process exited PID={pid}. Return code: {returncode}. ")
    logger.info("Killing bridge server...")
    kill_self_process()

  start_appium_process_in_bg(on_exit=on_exit)

  @asynccontextmanager
  async def lifespan(app: FastAPI):
    await wait_for_port_to_alive(
      APPIUM_SERVER_PORT,
      APPIUM_SERVER_HOST,
      timeout=60 if IS_RUNNING_IN_BRIDGE_APP else 15,
    )
    yield
    kill_process_by_port(APPIUM_SERVER_PORT, timeout=5)

  app = FastAPI(
    title="PantoAI QA Ext",
    lifespan=lifespan,
  )

  # Allow *.getpanto.ai, *.pantomax.co and localhost origins
  allow_origin_regex = r"(https://(([a-zA-Z0-9-]+\.)*pantomax\.co|([a-zA-Z0-9-]+\.)*getpanto\.ai)|http://localhost(:\d+)?)$"  # noqa: E501

  app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
  )
  app.include_router(misc_route)
  app.include_router(executor_route)
  app.include_router(action_router)
  app.include_router(screen_mirror_route)
  app.include_router(adb_router)
  return app


def start_bridge_server(host=SERVER_HOST, port=SERVER_PORT):
  try:
    app = create_app()
    uvicorn.run(
      app,
      host=host,
      port=port,
    )
  except DependencyNotInstalledError as e:
    logger.error(e)
  except Exception as e:
    logger.error(f"Failed to start server: {e}")


if __name__ == '__main__':
  deps.init()
  start_bridge_server()
