# Standard Library
from typing import Optional

# Third Party Imports
from pydantic import BaseModel


class Msg(BaseModel):
    id: Optional[str]
    msg: Optional[str]
    error: Optional[str]
