# edfh-data

Python library for the E:D Faction Hub application backend data services:

- EDDN listener service, receives messages from the EDDN stream and publishes them to a RabbitMQ exchange.
- EDDN handler service, polls message from a RabbitMQ queue, parses them and stores the relevant info in a relational database.

## Requirements

- Python 3.13 available in the sytem path.
- Running RabbitMQ and MariaDB instances (the included `docker-compose.yaml` file can set them up for development).

## Configuration

The following configuration variables are defined are defined as environment variables, or, for local development, specified in a `.env` configuration file:

```ini
DB_USER=dbuser
DB_PASSWD=<db_password>
DB_HOST=localhost
DB_PORT=3306
DB_NAME=edfh
RMQ_USER=rmquser
RMQ_PASSWD=<rabbitmq_password>
RMQ_HOST=localhost
RMQ_HANDLER_PREFETCH=10
```

## Usage

Install the package with the `eddn` extra:

```
python -m pip install edfh-data[eddn]
```

Launch the EDDN message handler service with:

```
eddn-handle
```

Launch the EDDN listener service with:

```
eddn-listen
```

## Development

### Python environment

Create a virtual environment using Python 3.13:

```
python3.13 -m venv .venv --prompt edfh-data --upgrade-deps
source .venv/bin/activate
```

Install the package in development mode along with the development dependencies:

```
python -m pip install -e .[dev]
```

Install pre-commit hooks:

```
pre-commit install
```

### Database service

Migrate the database with:

```
alembic upgrade head
```

Generate a new revision:

```
alembic revision --autogenerate -m "Revision message"
```
