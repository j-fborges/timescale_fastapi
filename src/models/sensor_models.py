from pydantic import BaseModel
from typing import List
from datetime import datetime, date


class SensorData(BaseModel):
    value: float
    timestamp: datetime


class SensorDataBatch(BaseModel):
    data: List[SensorData]


class SensorCreate(BaseModel):
    sensor_type: str
    description: str
    location: str


class SensorDailyStatsResponse(BaseModel):
    day: date
    sensor_id: int
    avg_value: float
    min_value: float
    max_value: float
    reading_count: int
    median_value: float
    iqr_value: float