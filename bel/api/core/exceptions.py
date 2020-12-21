# Standard Library
from typing import Any, Dict, Optional

# Third Party
from fastapi.exceptions import HTTPException as FastAPIHTTPException


class HTTPException(FastAPIHTTPException):
    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        user_flag: bool = False,
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.user_flag = user_flag
