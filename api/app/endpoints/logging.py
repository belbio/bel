# Standard Library
import enum
import logging
from typing import List, Optional

# Third Party Imports
from loguru import logger
from fastapi import APIRouter, Depends, HTTPException

# Local Imports
from pydantic import BaseModel

##### Models ###########
# https://gitlab.com/euri10/euri10_fastapi_base/blob/master/backend/app/models/loggers.py
#    Was this in separate models file for a reason?
# from models.loggers import LoggerModel, LoggerPatch


class LogLevelEnum(str, enum.Enum):

    critical = "critical"
    error = "error"
    warning = "warning"
    info = "info"
    debug = "debug"


class LoggerPatch(BaseModel):
    name: str
    level: LogLevelEnum


# from __future__ import annotations
# from typing import ForwardRef
# Pydantic issue: https://github.com/samuelcolvin/pydantic/issues/1370
# class LoggerModel(BaseModel):
#     name: str
#     level: Optional[int]
#     children: Optional[List[LoggerModel]] = []
# LoggerModel.update_forward_refs()


LOG_LEVELS = {
    "critical": logging.CRITICAL,
    "error": logging.ERROR,
    "warning": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG,
}


####### Router/endpoint/services ###############

router = APIRouter()


def get_lm_from_tree(loggertree: dict, find_me: str) -> dict:
    if find_me == loggertree["name"]:
        logger.debug("Found")
        return loggertree
    else:
        for ch in loggertree["children"]:
            logger.debug(f"Looking in: {ch['name']}")
            i = get_lm_from_tree(ch, find_me)
            if i:
                return i


def generate_tree() -> dict:

    # adapted from logging_tree package https://github.com/brandon-rhodes/logging_tree

    rootm = {
        "name": "root",
        "level": logging.getLevelName(logging.getLogger().getEffectiveLevel()),
        "children": [],
    }

    nodesm = {}
    items = list(logging.root.manager.loggerDict.items())  # type: ignore
    items.sort()
    for name, loggeritem in items:
        if isinstance(loggeritem, logging.PlaceHolder):
            nodesm[name] = nodem = {"name": name, "children": []}
        else:
            nodesm[name] = nodem = {
                "name": name,
                "level": logging.getLevelName(loggeritem.getEffectiveLevel()),
                "children": [],
            }

        i = name.rfind(".", 0, len(name) - 1)  # same formula used in `logging`
        if i == -1:
            parentm = rootm
        else:
            parentm = nodesm[name[:i]]
        parentm["children"].append(nodem)

    return rootm


@router.get("/loggers/{logger_name}", tags=["Admin"])
def logger_get(logger_name: str):
    """Get a specific logger"""

    rootm = generate_tree()
    lm = get_lm_from_tree(rootm, logger_name)
    if lm is None:
        raise HTTPException(status_code=404, detail=f"Logger {logger_name} not found")

    return lm


# @router.patch("/loggers", tags=["Admin"])
# def logger_patch(loggerpatch: LoggerPatch, current_user: User = Depends(get_current_active_user)):
#     """Change the loglevel dynamically for a specific logger"""

#     is_allowed(
#         current_user, "admin:tasks", autoraise=True, fail_msg="Not authorized to manage loggers"
#     )

#     rootm = generate_tree()
#     lm = get_lm_from_tree(rootm, loggerpatch.name)
#     logger.debug(f"Actual level of {lm['name']} is {lm['level']}")
#     logger.debug(f"Setting {loggerpatch.name} to {loggerpatch.level}")
#     logging.getLogger(loggerpatch.name).setLevel(LOG_LEVELS[loggerpatch.level])

#     return loggerpatch


@router.get("/loggers", tags=["Admin"])
def loggers_list():
    """Show all loggers and their loglevel settings"""

    rootm = generate_tree()

    return rootm
