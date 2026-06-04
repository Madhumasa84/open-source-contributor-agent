from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import github, health, providers, repositories, workflows
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.database import init_db
    await init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    description = (
        "A human-controlled, auditable AI platform for open-source contribution workflows."
    )
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description=description,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.allowed_origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(providers.router, prefix="/api")
    app.include_router(repositories.router, prefix="/api")
    app.include_router(workflows.router, prefix="/api")
    app.include_router(github.router, prefix="/api")
    return app


app = create_app()
