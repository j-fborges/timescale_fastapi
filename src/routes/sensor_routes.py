from fastapi import HTTPException, Path, Body, APIRouter, Depends
from src.database.postgres import get_postgres
from typing import Union, List
from asyncpg import Pool
from loguru import logger
from src.models.sensor_models import (
    SensorData,
    SensorDataBatch,
    SensorCreate,
    SensorDailyStatsResponse,
)

sensor_router = APIRouter()


@sensor_router.post("/sensors")
async def create_sensor(
    sensor: SensorCreate = Body(...), db: Pool = Depends(get_postgres)
):
    """
    Create a new sensor.

    Parameters
    ----------
    sensor : SensorCreate
        The sensor details (type, description, and location) to create.
    db : asyncpg.Pool
        Database connection pool injected by dependency.

    Returns
    -------
    dict
        A dictionary containing the newly created sensor ID and a success message.
    """
    insert_query = """
    INSERT INTO sensors (sensor_type, description, location)
    VALUES ($1, $2, $3)
    RETURNING sensor_id;
    """

    logger.info(
        f"Creating new sensor with type: {sensor.sensor_type}, location: {sensor.location}"
    )

    async with db.acquire() as conn:
        sensor_id = await conn.fetchval(
            insert_query, sensor.sensor_type, sensor.description, sensor.location
        )

    if sensor_id is None:
        logger.error("Failed to create sensor.")
        raise HTTPException(status_code=500, detail="Failed to create sensor")

    logger.info(f"Sensor created successfully with ID: {sensor_id}")
    return {"sensor_id": sensor_id, "message": "Sensor created successfully."}


@sensor_router.post("/sensor_data/{sensor_id}")
async def stream_sensor_data(
    sensor_id: int = Path(...),
    sensor_data: Union[SensorData, SensorDataBatch] = Body(...),
    db: Pool = Depends(get_postgres),
):
    """
    Stream sensor data (single or batch) for a specific sensor.

    Parameters
    ----------
    sensor_id : int
        The ID of the sensor to associate the data with.
    sensor_data : Union[SensorData, SensorDataBatch]
        The sensor data to stream, which can be either a single data point or a batch.
    db : asyncpg.Pool
        Database connection pool injected by dependency.

    Returns
    -------
    dict
        A success message once the data is streamed.
    """
    insert_query = """
    INSERT INTO sensor_data (sensor_id, value, time)
    VALUES ($1, $2, $3);
    """

    logger.info(f"Streaming data for sensor_id: {sensor_id}")

    async with db.acquire() as conn:
        async with conn.transaction():
            if isinstance(sensor_data, SensorDataBatch):
                for data in sensor_data.data:
                    logger.debug(f"Batch data: {data.value} at {data.timestamp}")
                    await conn.execute(
                        insert_query, sensor_id, data.value, data.timestamp
                    )
            elif isinstance(sensor_data, SensorData):
                logger.debug(
                    f"Single data: {sensor_data.value} at {sensor_data.timestamp}"
                )
                await conn.execute(
                    insert_query, sensor_id, sensor_data.value, sensor_data.timestamp
                )

    logger.info(f"Sensor data streamed successfully for sensor_id: {sensor_id}")
    return {"message": "Sensor data streamed successfully."}


@sensor_router.get(
    "/daily_avg/{sensor_id}", response_model=List[SensorDailyStatsResponse]
)
async def get_sensor_daily_avg(
    sensor_id: int = Path(..., description="The ID of the sensor"),
    db: Pool = Depends(get_postgres),
):
    """
    Query daily statistics (min, max, median, IQR) for a specific sensor over the last 7 days.

    Parameters
    ----------
    sensor_id : int
        The ID of the sensor.
    db : asyncpg.Pool
        Database connection pool injected by dependency.

    Returns
    -------
    List[SensorDailyStatsResponse]
        A list of daily sensor statistics (average, min, max, median, IQR).
    """

    query = """
    WITH sensor_stats AS (
        SELECT
            time_bucket('1 day', time) AS day,
            sensor_id,
            avg(value) AS avg_value,
            min(value) AS min_value,
            max(value) AS max_value,
            count(*) AS reading_count,
            percentile_cont(0.5) WITHIN GROUP (ORDER BY value) AS median_value,
            percentile_cont(0.75) WITHIN GROUP (ORDER BY value) -
            percentile_cont(0.25) WITHIN GROUP (ORDER BY value) AS iqr_value
        FROM sensor_data
        WHERE sensor_id = $1
        GROUP BY day, sensor_id
    )
    SELECT * FROM sensor_stats
    ORDER BY day DESC
    LIMIT 7;
    """

    async with db.acquire() as conn:
        rows = await conn.fetch(query, sensor_id)

    if not rows:
        raise HTTPException(status_code=404, detail="No data found for this sensor.")

    return [
        SensorDailyStatsResponse(
            day=row["day"],
            sensor_id=row["sensor_id"],
            avg_value=row["avg_value"],
            min_value=row["min_value"],
            max_value=row["max_value"],
            reading_count=row["reading_count"],
            median_value=row["median_value"],
            iqr_value=row["iqr_value"],
        )
        for row in rows
    ]