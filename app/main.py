import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import auth, checkin, explorer, route
from app.core.config import settings
from app.core.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version='1.0.0',
    description='Sacred heritage routing platform for Kyrgyzstan with AI nomadic guidance.',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception('Unhandled error on %s: %s', request.url.path, exc)
    return JSONResponse(status_code=500, content={'detail': 'Internal server error'})


app.include_router(auth.router)
app.include_router(route.router)
app.include_router(checkin.router)
app.include_router(explorer.router)


@app.on_event('startup')
async def log_runtime_context() -> None:
    logger.info('Runtime app file: %s', Path(__file__).resolve())
    logger.info('Registered routes: %s', [r.path for r in app.routes])


@app.get('/health', tags=['system'])
async def health() -> dict[str, str]:
    return {'status': 'ok', 'service': settings.APP_NAME}
