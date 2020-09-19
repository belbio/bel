# Standard Library
import inspect
import json
import os
import pathlib
import sys
from typing import List, Mapping

"""NOTES

* Any settings that have SECRET, TOKEN, PASSWD, PASSWORD - will not be exposed
  via the show_settings() function used by the BEL API /settings endpoint
* Only UPPER CASED settings will be exposed via show_settings()

Examples
    SMTP_TLS =
    _boolean("SMTP_TLS", True)
    _SMTP_PORT = os.getenv("SMTP_PORT")
    if _SMTP_PORT is not None:
        SMTP_PORT = int(_SMTP_PORT)
    SMTP_HOST = os.getenv("SMTP_HOST")
"""

LOG_LEVEL = os.getenv("LOGGING", default="INFO")
LOG_SERIALIZE = False
SERVER_MODE = os.getenv("SERVER_MODE", default="PROD")
HOST_NAME = os.getenv("HOST_NAME", default="hostname_not_set")


def getenv_boolean(var_name, default=False):
    result = default
    env_value = os.getenv(var_name)
    if env_value is not None:
        result = env_value.upper() in ("TRUE", "1")
    return result


# app directory (./bel (parent to ./bel/core settings.py directory))
# filename = inspect.getframeinfo(inspect.currentframe()).filename
appdir = pathlib.Path(__file__).resolve().parent.parent
rootdir = pathlib.Path(appdir).parent  # parent to ./lib/bel directory


# Mailgun settings
MAIL_API = os.getenv("MAIL_API", default=None)
MAIL_API_KEY = os.getenv("MAIL_API_KEY")
MAIL_FROM = os.getenv("MAIL_FROM")

# Auth Settings
SECURE = getenv_boolean("SECURE", default=False)
if SECURE:
    JWT_SECRET = os.getenv("JWT_SECRET", default=None)
    if JWT_SECRET is None:
        print("Cannot start with SECURE=True and no JWT_SECRET")
        sys.exit()

CORS_ORIGINS = os.getenv("CORS_ORIGINS", default="*")
if CORS_ORIGINS:
    CORS_ORIGINS = CORS_ORIGINS.split(",")

service_name = "BEL"

# Swagger/OpenAPI settings
OPENAPI_TITLE = f"{service_name}"
OPENAPI_DESC = f"""
{service_name} API Endpoint Documentation
"""

# BEL API
BEL_API = os.getenv("BEL_API", default="http://localhost:8888")

# Redis Info
REDIS_HOST = os.getenv("REDIS_HOST", default="localhost")
REDIS_PORT = os.getenv("REDIS_PORT", default=6379)
REDIS_QUEUE = os.getenv("NANOPUBSTORE_TYPE", default="belservice")

# Elasticsearch Info
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", default="http://localhost:9200")
TERMS_INDEX = os.getenv("TERMS_INDEX", default="terms2")  # Elasticsearch terms index
TERMS_DOCUMENT_TYPE = os.getenv("TERMS_DOCUMENT_TYPE", default="term")

# Arango Databases
ARANGO_URL = os.getenv("ARANGO_URL", default="http://localhost:8529")
ARANGO_USER = os.getenv("ARANGO_USER", default="root")
ARANGO_PASSWORD = os.getenv("ARANGO_PASSWORD", default="Set a password, please")

BEL_DB = os.getenv("BEL_DB", default="bel")
RESOURCES_DB = os.getenv("RESOURCES_DB", default="bel")


# BEL Language Settings
species_entity_types = ["Gene", "Protein", "RNA", "Micro_RNA"]

BEL_DEFAULT_VERSION = os.getenv("BEL_DEFAULT_VERSION", default="latest")

BEL_SPECIFICATION_URLS = json.loads(os.getenv("BEL_SPECIFICATION_URLS", default="{}"))
if not BEL_SPECIFICATION_URLS:
    BEL_SPECIFICATION_URLS = [
        "http://resources.bel.bio.s3-us-east-2.amazonaws.com/specifications/bel_latest.yaml"
    ]

bel_canonicalize_default = {
    "HGNC": ["EG", "SP"],
    "MGI": ["EG", "SP"],
    "RGD": ["EG", "SP"],
    "ZFIN": ["EG", "SP"],
    "SP": ["EG"],
    "CHEMBL": ["CHEBI"],
    "SCOMP": ["GO"],
    "SCHEM": ["CHEBI", "MESH"],
}

bel_decanonicalize_default = {
    "EG": ["HGNC", "MGI", "RGD", "ZFIN", "SP"],
    "SP": ["HGNC", "MGI", "RGD", "ZFIN"],
    "SCOMP": ["GO"],
    "SCHEM": ["CHEBI", "MESH"],
}

BEL_CANONICALIZE: Mapping[str, List[str]] = json.loads(os.getenv("BEL_CANONICALIZE", default="{}"))
if not BEL_CANONICALIZE:
    BEL_CANONICALIZE = bel_canonicalize_default


BEL_DECANONICALIZE: Mapping[str, List[str]] = json.loads(
    os.getenv("BEL_DECANONICALIZE", default="{}")
)
if not BEL_DECANONICALIZE:
    BEL_DECANONICALIZE = bel_decanonicalize_default

# Boost these namespaces in term search results and completions
BEL_BOOST_NAMESPACES = json.loads(os.getenv("BEL_BOOST_NAMESPACES", default="{}"))
if not BEL_BOOST_NAMESPACES:
    BEL_BOOST_NAMESPACES = ["HGNC", "MGI", "RGD", "ZFIN", "CHEBI", "GO"]

BEL_ORTHOLOGIZE_TARGETS = json.loads(os.getenv("BEL_ORTHOLOGIZE_TARGETS", default="{}"))
if not BEL_ORTHOLOGIZE_TARGETS:
    BEL_ORTHOLOGIZE_TARGETS = []

BEL_FILTER_SPECIES = json.loads(os.getenv("BEL_FILTER_SPECIES", default="{}"))
if not BEL_FILTER_SPECIES:
    BEL_FILTER_SPECIES = []
