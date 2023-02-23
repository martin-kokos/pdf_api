# pdf_api
PDF content extraction API.

## Schema
Swagger/OpenAPI: `http://localhost/docs`  
Redoc: `http://localhost/redoc`

# Docker
## Build
`docker build -t pdf_api:latest .`

## Run
`docker run -p 80:80 pdf_api:latest`

# Develop
Install requirements:
`poetry install`

Activate venv:
`poetry shell`

## Test
`poetry run pytest`
