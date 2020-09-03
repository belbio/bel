"""info.py
Informational endpoints
"""

# Third Party Imports
import fastapi
from loguru import logger
from fastapi import APIRouter, Depends
import re

# Local Imports
import bel.core.settings as settings
import bel.terms.terms
from bel.__version__ import __version__ as bel_lib_version
from bel.schemas.info import Status, Version


router = APIRouter()


@router.get("/status", tags=["Info"], response_model=Status)
def get_status():
    """Get status"""

    status = {
        "state": "OK",
        "bel_lib_version": bel_lib_version,
        "fastapi_version": fastapi.__version__,
        # "settings": settings.show_settings(),
        # "elasticsearch_stats": bel.terms.terms.namespace_term_counts(),
    }

    return status


@router.get("/version", tags=["Info"], response_model=Version)
def get_version():
    """Get Version"""

    return {"version": bel_lib_version}


# @router.get("/settings", tags=["Info"], response_model=dict)
# def get_settings():
#     """ Settings

#     Any uppercased attributes in the settings module will be exposed in this endpoint.
#     Any settings.secrets that are cast as a Secret will be masked.
#     Any URLs that are cast as a URL will have embedded passwords in the url string masked.
#     """

#     return settings.show_settings()


@router.get("/ping", tags=["Info"])
def ping() -> dict:
    """Check service - no authentication/token required"""

    return {"running": True}


@router.get("/settings", tags=["Info"], response_model=dict)
def get_settings():
    """ Settings

    Only show UPPER_CASED settings that do not have ['SECRET', 'TOKEN', 'PASSWORD', 'PASSWD'] in the name
    """

    """Show settable settings via .env file or environment

    - Only show UPPER_CASED settings that do not have ['SECRET', 'TOKEN', 'PASSWORD', 'PASSWD'] in the name
    """

    skip_list = ["SECRET", "TOKEN", "PASSWD", "PASSWORD"]
    try:
        s = {
            var: getattr(settings, var)
            for var in dir(settings)
            if var.isupper() and not re.search("SECRET|TOKEN|PASSWD|PASSWORD", var)
        }

    except Exception as e:
        print("Error", str(e))
    return s
