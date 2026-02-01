from adbutils import adb  # type:ignore
from fastapi import APIRouter
from pydantic import BaseModel


class ADBDeviceList(BaseModel):
  serial_no: str


router = APIRouter()


@router.post("/get-devices", response_model=list[ADBDeviceList])
async def get_available_devices():
  devices = adb.device_list()
  return [ADBDeviceList(serial_no=d.serial) for d in devices]
