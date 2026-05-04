from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.database.postgres import init_postgres, close_postgres
from src.routes.sensor_routes import sensor_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    await init_postgres()   # Called on startup
    yield
    await close_postgres()  # Called on shutdown


app: FastAPI = FastAPI(
    lifespan=lifespan,
    title="FastAPI TimescaleDB Sensor Data API",
    description="High-performance API for streaming and querying sensor data using TimescaleDB",
    version="1.0.0"
)

app.include_router(sensor_router)