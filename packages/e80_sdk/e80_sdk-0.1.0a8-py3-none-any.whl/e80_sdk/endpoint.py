import logging
from . import fastapi
from e80_sdk.internal.httpx_async import async_client
from contextlib import asynccontextmanager
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

logger = logging.getLogger(__name__)

reload_jwt_task = None

_EIGHTY80_HEALTH_CHECK_PATH = "/.8080/health"


def eighty80_app() -> fastapi.FastAPI:
    global reload_jwt_task  # TODO: Remove this global.

    eighty80_app = fastapi.FastAPI()
    FastAPIInstrumentor.instrument_app(
        eighty80_app,
        excluded_urls=_EIGHTY80_HEALTH_CHECK_PATH,
    )

    eighty80_app.get(_EIGHTY80_HEALTH_CHECK_PATH)(_eighty80_health_check)

    return eighty80_app


async def _eighty80_health_check():
    return {"status": "ok"}


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    yield
    await async_client.aclose()
