from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.persistence.database import initialize_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Audit Log Service",
    description="Tamper-evident append-only audit log service",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)