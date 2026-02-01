from pydantic import BaseModel


class Action(BaseModel):
  action_type: str
  params: dict | None = None
