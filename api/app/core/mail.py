# Local Imports
from bel.Config import config
from bel.utils import http_client


def send_mail(
    mail_to: str, subject: str, msg: str, mail_from: str = config["bel_api"]["mail"]["admin_email"]
):
    """Send mail using MailGun API"""

    data = {"to": mail_to, "from": mail_from, "subject": subject, "text": msg}

    request = http_client.post(
        f"{config['bel_api']['mail']['api']}/messages",
        auth=("api", config["secrets"]["bel_api"]["mail"]["api_key"]),
        data=data,
    )
    return request
