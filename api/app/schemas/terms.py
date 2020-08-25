# Third Party Imports
# Standard Library
import enum
from typing import Any, List, Mapping, Optional, Union

# Local Imports
from pydantic import BaseModel, Field
from bel.schemas.terms import Term, TermCompletion


class TermCompletionResponse(BaseModel):
    completion_text: str = Field(..., description="String used for term completions")
    completions: List[TermCompletion]
