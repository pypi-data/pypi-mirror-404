# NoBS Python

Define your architecture in pure Python-servers, workers, scheduled jobs, and databases connect automatically through type hints.

## Overview

NoBS is a Python framework that eliminates configuration overhead by using type hints to automatically wire up your infrastructure. Write pure Python code and let NoBS handle the connections between servers, workers, databases, and scheduled jobs.

No YAML. No configuration files. Just Python.

## Features

- **Type-hint driven** - Your type annotations define your architecture
- **Automatic dependency injection** - Components connect without manual wiring
- **Pure Python** - Everything is code, nothing is configuration
- **Full IDE support** - Autocomplete and type checking work out of the box
- **Minimal boilerplate** - Focus on your logic, not setup

## Installation
```bash
pip install nobs
```

## Quick Start
```python
from takk.models import Project, FastAPIApp, Worker
from takk.secrets import SlackWebhook

from my_app.settings import AppSettings
from my_app import app

background_worker = Worker("background")

project = Project(
    name="my-custom-server",
    shared_settings=[AppSettings],

    workers=[background_worker],

    my_server=FastAPIApp(app),
)
```

## How It Works

NoBS uses Python type hints to understand your application's resources and automatically creates the necessary connections. When you annotate a settings class with a type like `PostgresDsn`or `RedisDsn`, NoBS:

1. Detects the dependency through type
2. Instantiates the component with appropriate configuration
3. Injects it into your environment

Read the [full article](https://docs.takkthon.com/blog/deploy-with-python-type-hints) to see how we built this approach.

## Core Components

### Server
```python
from takk.models import Project, FastAPIApp, Worker
from takk.secrets import SlackWebhook

project = Project(
    name="my-custom-server",

    custom_network_app=NetworkApp(
        command=["/bin/bash", "-c", "uv run main.py"],
        port=8000,
    ),
)
```

### Worker
```python
from takk import Worker

worker = Worker("name-of-worker")

worker.run(function, Args(...))
```

### Database
```python
from pydantic import PostgresDsn, RedisDsn, BaseModel
from takk import Database

class MyAppSettings(BaseModel):
    redis_url: RedisDsn
    psql_db: PostgresDsn
```

### Scheduled Jobs
```python
from takk.models import Compute, Project, Job

from my_app.train import train_model, TrainConfig

project = Project(
    name="ml-example",

    train_pokemon_model=Job(
        train_model,
        cron_schedule="0 3 * * *",  # Runs daily at 3 AM
        arguments=TrainConfig(...),
    ),
)
```

## Requirements

- Python 3.10+
- Type hints support

## Development

### Setup
```bash
git clone https://gitlab.com/MatsMoll/nobs.git
cd nobs

python -m venv .venv
source .venv/bin/activate

uv sync
```

### Running Tests
```bash
pytest
```

### Type Checking
```bash
mypy nobs
```

## Examples

Check out the [examples directory](examples/) for complete applications:

- [Simple web server](examples/web_server/)
- [Background worker with scheduling](examples/worker/)
- [Full-stack application](examples/fullstack/)

## Why nobs?

Traditional frameworks require configuration files, manual wiring, and boilerplate code. nobs leverages Python's type system to eliminate this overhead:

**Before (traditional approach):**
```yaml
# config.yaml
database:
  host: localhost
  port: 5432
```

**After (takk):**
```python
class MyApp(BaseModel):
    psql_uri: PostgresDsn
```

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md).

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Add tests for your changes
4. Ensure all tests pass (`pytest`)
5. Submit a pull request

## Learn More

- [Documentation](https://docs.takkthon.com/docs)
