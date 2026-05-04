# Sensor Data API with FastAPI + TimescaleDB

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)\](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)\](https://fastapi.tiangolo.com/)
[![TimescaleDB](https://img.shields.io/badge/TimescaleDB-2.15-orange)\](https://www.timescale.com/)

High‑performance REST API for streaming, storing, and querying time‑series sensor data. Built with FastAPI, PostgreSQL + TimescaleDB extension (hypertables), and deployed with Docker + AWS ECS (coming soon).

## Features

- **Stream sensor data** – single or batch ingestion (`POST /sensor_data/{sensor_id}`)
- **Sensor management** – create new sensors (`POST /sensors`)
- **Time‑series analytics** – daily aggregates: average, min, max, median, interquartile range (IQR) using TimescaleDB’s `time_bucket` and percentile functions
- **Async & high performance** – asyncpg connection pooling, FastAPI async endpoints
- **Auto‑generated API documentation** – Swagger UI and ReDoc
- **Container ready** – Dockerfile included (to be added)

## Tech Stack

| Layer       | Technology |
|-------------|------------|
| API Framework | FastAPI (Python) |
| ASGI Server  | Uvicorn |
| Database     | PostgreSQL 15 + TimescaleDB extension (via Neon serverless) |
| DB Driver    | asyncpg (asynchronous) |
| Environment  | Python-dotenv |
| Logging      | Loguru |
| Deployment   | Docker, GitHub Actions, AWS ECS (planned) |

## Architecture

The sensor data table is stored as a **TimescaleDB hypertable**, which automatically partitions data into time‑based chunks for fast inserts and queries. The API uses a connection pool to handle many concurrent requests.

![Architecture diagram placeholder](docs/architecture.png)

## Prerequisites

- Python 3.12+
- `uv` (fast Python package manager) – install with `pip install uv`
- A [Neon](https://neon.tech) PostgreSQL account (free tier)
- Optional: `httpie` for testing (`uv pip install httpie`)

## Setup & Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/timescale_fastapi.git
   cd timescale_fastapi
   ```

2. **Create virtual environment and install dependencies**
   ```bash
   uv venv
   source .venv/bin/activate   # Linux/macOS
   uv add python-dotenv asyncpg loguru fastapi uvicorn requests
   ```

3. **Configure environment variables**  
   Create a `.env` file in the project root:
   ```
   DATABASE_URL=postgresql://user:password@host.neon.tech/neondb?sslmode=require
   ```
   Replace with your Neon connection string (find it in Neon Console → Connect).

4. **Initialize the database**  
   Run the following SQL in Neon’s SQL Editor:
   ```sql
   CREATE EXTENSION IF NOT EXISTS timescaledb;

   CREATE TABLE IF NOT EXISTS sensors (
       sensor_id SERIAL PRIMARY KEY,
       sensor_type VARCHAR(50) NOT NULL,
       description VARCHAR(255),
       location VARCHAR(255)
   );

   CREATE TABLE IF NOT EXISTS sensor_data (
       sensor_id INT REFERENCES sensors(sensor_id),
       value FLOAT NOT NULL,
       time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
       PRIMARY KEY(sensor_id, time)
   );

   SELECT create_hypertable('sensor_data', 'time');
   ```
   (Optionally insert sample data – see [sample_data.sql](docs/sample_data.sql))

5. **Run the API**
   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
   ```
   Visit `http://localhost:8080/docs` for interactive documentation.

## API Endpoints

### 1. Create a new sensor

**POST** `/sensors`

Request body:
```json
{
  "sensor_type": "temperature",
  "description": "Living room temperature sensor",
  "location": "Living Room"
}
```

Response:
```json
{
  "sensor_id": 3,
  "message": "Sensor created successfully."
}
```

Test with `httpie`:
```bash
http POST http://localhost:8080/sensors sensor_type="temperature" description="Living room sensor" location="Living Room"
```

---

### 2. Stream single sensor data point

**POST** `/sensor_data/{sensor_id}`

Path parameter: `sensor_id` (integer)

Request body (single reading):
```json
{
  "value": 23.5,
  "timestamp": "2025-05-01T14:29:00"
}
```

Response:
```json
{
  "message": "Sensor data streamed successfully."
}
```

Example:
```bash
http POST http://localhost:8080/sensor_data/3 value:=23.5 timestamp="2025-05-01T14:29:00"
```

---

### 3. Stream batch of sensor data points

**POST** `/sensor_data/{sensor_id}`

Request body (batch):
```json
{
  "data": [
    {"value": 22.5, "timestamp": "2025-05-01T14:30:00"},
    {"value": 22.7, "timestamp": "2025-05-01T14:31:00"}
  ]
}
```

Response same as single.

Example:
```bash
http POST http://localhost:8080/sensor_data/3 data:='[{"value": 22.5, "timestamp": "2025-05-01T14:30:00"}, {"value": 22.7, "timestamp": "2025-05-01T14:31:00"}]'
```

---

### 4. Get daily statistics (last 7 days)

**GET** `/daily_avg/{sensor_id}`

Path parameter: `sensor_id`

Response:
```json
[
  {
    "day": "2025-05-01",
    "sensor_id": 3,
    "avg_value": 22.6,
    "min_value": 22.5,
    "max_value": 22.7,
    "reading_count": 2,
    "median_value": 22.6,
    "iqr_value": 0.2
  }
]
```

Example:
```bash
http GET http://localhost:8080/daily_avg/3
```

## Database Schema & TimescaleDB

- `sensors` – metadata for each sensor device.
- `sensor_data` – hypertable partitioned by `time`. Primary key is `(sensor_id, time)` – optimised for time‑range queries on a single sensor.

TimescaleDB provides:
- `time_bucket('1 day', time)` – aggregate data into daily buckets.
- `percentile_cont()` – compute median and IQR directly in SQL.

## Project Structure

```
timescale_fastapi/
├── .env                  # Database credentials (ignored by git)
├── .gitignore
├── README.md
├── pyproject.toml        # Dependencies (managed by uv)
├── uv.lock
├── src/
│   ├── database/
│   │   └── postgres.py   # Connection pool & lifecycle
│   ├── models/
│   │   └── sensor_models.py   # Pydantic schemas
│   ├── routes/
│   │   └── sensor_routes.py   # API endpoints
│   └── main.py           # FastAPI app entrypoint
└── tests/                # (coming soon)
```

## Development & Testing

- Run the server with auto‑reload: `uvicorn src.main:app --reload`
- Run tests (if added): `pytest` (not yet implemented)
- Use the auto‑generated Swagger UI at `http://localhost:8080/docs`

## Deployment (planned)

The project will be containerised with Docker and deployed to:

- **AWS ECS (Fargate)** using GitHub Actions CI/CD, or
- **Local Kubernetes simulation** with Minikube for learning orchestration.

Dockerfile and Kubernetes manifests will be added in a future commit.

## License

MIT (or choose your own)

## Acknowledgements

- Inspired by the official TimescaleDB + FastAPI tutorial.
- Built with `uv`, `asyncpg`, and Neon's free tier.