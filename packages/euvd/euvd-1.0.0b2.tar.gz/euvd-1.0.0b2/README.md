# EUVD - European Union Vulnerabilities Database python wrapper

This library provides a Python wrapper for the EUVD API, offering a streamlined and consistent way to interact with the service. It is particularly useful for integrating the service into other applications.

## Installation

The library can be installed using `pip`:

```bash
pip install euvd
```

## Usage

### Clients

The `euvd.clients` module provides Python clients for interacting with the European Union Vulnerabilities Database (EUVD) API. These clients offer methods for retrieving vulnerabilities, advisories, and performing tailored searches with filters.

#### Synchronous Client

```python
from euvd.clients import EUVDSyncClient
from euvd.models import EnisaVulnerability

with EUVDSyncClient() as client:
    vulnerabilities: list[EnisaVulnerability] = client.get_latest_vulnerabilities()
    print(vulnerabilities)
```

#### Asynchronous Client

```python
import asyncio
from euvd.clients import EUVDAsyncClient
from euvd.models import EnisaVulnerability

async def main():
    async with EUVDAsyncClient() as client:
        vulnerabilities: list[EnisaVulnerability] = await client.get_latest_vulnerabilities()
        print(vulnerabilities)

asyncio.run(main())
```

### Data models

The library provides a `euvd.models` package with several classes to encapsulate the different data structures used by the API.

## Development

This library uses modern Python tooling for quality assurance:

- **Testing**: pytest with comprehensive test coverage
- **Type checking**: mypy with strict mode enabled
- **Linting**: ruff for code quality and formatting
- **Multi-version testing**: tox for testing across Python 3.11-3.14

### Running tests

```bash
# Run tests for your Python version
pytest tests

# Run tests across all supported Python versions
tox

# Run linting
ruff check euvd

# Run type checking
mypy euvd
```

## Official documentation

Refer to the official documentation for detailed information about the methods and their parameters.

## Disclaimer

This is beta software, not recommended yet for production use.

As the actual EUVD API is in beta stage and prone to change, this library may stop working without warning.

Also, as there is no official documentation on the data structures used, the model structures and semantics were reverse-engineered and may contain errors.

## License

This library is licensed under the MIT License.
