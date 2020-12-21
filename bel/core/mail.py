# Standard Library
from typing import List

# Third Party
import requests
from loguru import logger

# Local
import bel.core.settings as settings


def send_simple_email(to: List[str], subject: str, body: str, body_html: str = ""):
    """Send email to user"""

    data = {
        "from": f"BioDati Admin <{settings.MAIL_FROM}>",
        "to": to,
        "subject": subject,
        "text": body,
    }

    if body_html:
        data["html"] = body_html

    r = requests.post(
        f"{settings.MAIL_API}/messages",
        auth=("api", settings.MAIL_API_TOKEN),
        data=data,
    )

    if r.status_code != 200:
        logger.error(f"")
    else:
        logger.info(f"Emailed {to} about {subject}")

    return r
