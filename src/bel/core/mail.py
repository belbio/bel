# Standard Library
from typing import List

# Third Party Imports
import requests
from loguru import logger

# Local Imports
import bel.core.settings as settings


def send_simple_email(to: List[str], subject: str, body: str):
    """Send email to user"""

    r = requests.post(
        f"{settings.MAIL_API}/messages",
        auth=("api", settings.MAIL_API_KEY),
        data={
            "from": f"BioDati Admin <{settings.MAIL_FROM}>",
            "to": to,
            "subject": subject,
            "text": body,
        },
    )

    logger.info(f"Emailed {to} about {subject}")

    return r
