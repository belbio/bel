# Standard Library
from typing import Optional, Union

# Third Party
from pydantic import BaseModel, Field


class Version(BaseModel):
    version: str
