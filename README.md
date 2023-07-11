# pdf_api
PDF content extraction API.

## Schema
Swagger/OpenAPI: `http://localhost:8000/docs`  
Redoc: `http://localhost:8000/redoc`

# Docker

## App with DB

# Develop
## Environment
Install requirements:

`poetry install`

Activate venv:

`poetry shell`

## DB
### start test DB:
`docker run --name test-postgres -p 5432:5432 -e POSTGRES_USERNAME=postgres -e POSTGRES_PASSWORD=postgres postgres` \
`export DB_DSN="postgresql+psycopg://postgres:postgres@localhost:5432/postgres"` \
`export JWT_SECRET="secret"` \
### connect:
`psql -d "host=localhost port=5432 user=postgres password=postgres"` \
### bootstrap tables:
`alembic upgrade head`
### upgrade tables:
`docker exec pdf_api-web-1 alembic upgrade head`

### Docker
`docker build -t pdf_api:latest .`
`docker run -p 8080:80 pdf_api:latest`

### App
`poetry run uvicorn pdf_api.app:app --host 0.0.0.0 --port 8080 --reload`

### Pyest
Pytest uses sqlite

`poetry run pytest -xvs --ff`

## Run
`docker compose -f docker-compose.yml up --build`
