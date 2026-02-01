from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from pantoqa_bridge.models.misc import Action
from pantoqa_bridge.utils.service_manager import get_service

router = APIRouter()


class ActionRequestModel(BaseModel):
  id: str
  action: Action
  device_serial_no: str | None = None


class ActionResponseModel(BaseModel):
  id: str
  type: str
  data: Any | None = None


@router.post('/perform-action', response_model=ActionResponseModel)
async def perform_action(request: ActionRequestModel):
  srv = get_service(request.device_serial_no)
  result = srv.process(request.action)

  return ActionResponseModel(
    id=request.id,
    type="driver_action_response",
    data=result,
  )
