# Standard Library
from datetime import datetime, timedelta

# Third Party
import jwt
from loguru import logger

# Local
from bel.Config import config

jwt_algorithm = "HS256"


def jwt_create(userid, payload, expiration=None):
    """Create a JSON Web Token
    payload: dictionary to be added to JWT
    expiration:  number of seconds from now to expire token -- defaults to 3600 seconds

    """

    if expiration:
        exp = datetime.utcnow() + timedelta(seconds=expiration)
    else:
        exp = datetime.utcnow() + timedelta(seconds=3600)

    additional_payload = {
        "sub": userid,
        "exp": exp,
        "iat": datetime.utcnow(),
    }

    logger.debug("UserId: ", userid, " Payload: ", payload)

    payload.update(additional_payload)
    token = jwt.encode(
        payload, config["secrets"]["bel_api"]["shared_secret"], algorithm=jwt_algorithm
    )

    return token.decode("utf-8")


def jwt_validate(token):
    """Validates JSON Web Token
    Returns:
        valid:          boolean - true if valid token
        token_payload:  dict of token payload
    """
    try:
        jwt.decode(token, config["secrets"]["bel_api"]["shared_secret"], algorithm=jwt_algorithm)
        return True
    except Exception as e:
        return False


def jwt_extract(token):
    logger.debug("In JWT Extract")
    try:
        return (
            jwt.decode(
                token, config["secrets"]["bel_api"]["shared_secret"], algorithm=jwt_algorithm
            ),
            "",
        )
    except jwt.ExpiredSignatureError:
        logger.debug("JWT expired")
        return None, "JWT expired"
    except Exception as e:
        logger.debug("JWT extraction error ", e)
        return None, e
