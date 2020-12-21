#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library
import os
import sys
import time

# Third Party
from fastapi import FastAPI
from fastapi import __version__ as fastapi_version
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.wsgi import WSGIMiddleware
from starlette.requests import Request
from starlette.staticfiles import StaticFiles
from starlette_prometheus import PrometheusMiddleware, metrics

# Local
import bel.core.settings as settings
from bel.__version__ import __version__ as version
from bel.api.core.middleware import StatsMiddleware
from bel.api.endpoints.bel import router as bel_router
from bel.api.endpoints.belspec import router as belspec_router
from bel.api.endpoints.info import router as info_router
from bel.api.endpoints.nanopubs import router as nanopubs_router
from bel.api.endpoints.orthology import router as orthology_router
from bel.api.endpoints.pubmed import router as pubmed_router
from bel.api.endpoints.terms import router as terms_router

logger.remove()

LOG_SERIALIZE = os.getenv("LOG_SERIALIZE", default=None)
LOG_LEVEL = os.getenv("LOG_LEVEL", default="INFO")

if LOG_SERIALIZE is not None:
    logger.start(sys.stderr, serialize=True, enqueue=True)
else:
    logger.start(sys.stderr, colorize=True, level=LOG_LEVEL, enqueue=True)
    # logger.start(
    #     sys.stderr,
    #     colorize=True,
    #     format="{time} {level} {file} {line} <c>{message}</c>",
    #     level=LOG_LEVEL,
    # )

    logger.disable("__mp_main__")


# FastAPI API routing structure
app = FastAPI(
    title=settings.OPENAPI_TITLE,
    description=settings.OPENAPI_DESC,
    openapi_url="/openapi.json",
    version=version,
)

# Added user_flag to HTTPException
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    headers = getattr(exc, "headers", None)
    if headers:
        return JSONResponse(
            {"detail": exc.detail, "user_flag": exc.user_flag},
            status_code=exc.status_code,
            headers=headers,
        )
    else:
        return JSONResponse(
            {"detail": exc.detail, "user_flag": exc.user_flag}, status_code=exc.status_code
        )


logger.info("Starting BEL API")
logger.info(f"Fast API Version: {fastapi_version}")

rootdir = os.path.split(__file__)[0]

# Static resources
app.mount("/static", StaticFiles(directory=f"{rootdir}/static"), name="static")

app.include_router(info_router)
app.include_router(bel_router, prefix="/bel", tags=["BEL"])
app.include_router(nanopubs_router)
app.include_router(pubmed_router, tags=["Pubmed"])
app.include_router(terms_router, prefix="/bel", tags=["BEL Terms"])
app.include_router(orthology_router, prefix="/bel", tags=["Orthology"])
app.include_router(belspec_router, tags=["BEL Specifications"])


###############################################################################
# Middleware
###############################################################################

# GZIP
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Prometheus metrics
app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics/", metrics)

# Stats
app.add_middleware(StatsMiddleware)


if __name__ == "__main__":
    # Third Party
    import dotenv
    import uvicorn

    dotenv.load_dotenv()

    # debug=true may not automatically reload the code after history - may need
    # to run uvicorn from command line directly and not programmatically
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        reload=True,
        reload_dirs=[".", "../../lib/bel"],
        port=8888,
        debug=True,
        workers=2,
        log_level="critical",
        access_log=False,
    )
