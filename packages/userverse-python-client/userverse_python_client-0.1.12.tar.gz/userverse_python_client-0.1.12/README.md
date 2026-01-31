



<!-- CI status for your release workflow -->

[![CI - Release Tag](https://github.com/SoftwareVerse/userverse-python-client/actions/workflows/release.yml/badge.svg)](https://github.com/SoftwareVerse/userverse-python-client/actions/workflows/release.yml)

<!-- Latest release (SemVer-aware) badge → opens the latest release page -->

[![Latest Release](https://img.shields.io/github/v/release/SoftwareVerse/userverse-python-client?display_name=tag&sort=semver)](https://github.com/SoftwareVerse/userverse-python-client/releases/latest)

<!-- Optional: latest tag badge (from tags, even if not “GitHub Release”) -->

[![Latest Tag](https://img.shields.io/github/v/tag/SoftwareVerse/userverse-python-client?label=tag&sort=semver)](https://github.com/SoftwareVerse/userverse-python-client/releases/latest)

<!-- Optional: release date & total downloads badges -->

[![Release Date](https://img.shields.io/github/release-date/SoftwareVerse/userverse-python-client)](https://github.com/SoftwareVerse/userverse-python-client/releases/latest)


<!-- Optional: release date & total downloads badges -->
[![Downloads](https://img.shields.io/github/downloads/SoftwareVerse/userverse-python-client/total)](https://github.com/SoftwareVerse/userverse-python-client/releases)

<!-- You already have Codecov; keep it (replace token if needed) -->

[![codecov](https://codecov.io/gh/SoftwareVerse/userverse-python-client/branch/main/graph/badge.svg?token=YOUR_TOKEN)](https://codecov.io/gh/SoftwareVerse/userverse-python-client)

# userverse-python-client

Python client for the Userverse HTTP server.

## Installation

Install from PyPI:

```bash
python -m pip install userverse-python-client
```

For editable installs from source, see the repository README:
https://github.com/SoftwareVerse/userverse-python-client#installation

## Usage

The main package is `userverse_python_client`, which exposes `UverseUserClient`:

```python
from userverse_python_client import UverseUserClient

client = UverseUserClient(base_url="https://api.example.com")
```

## Demo

The runnable demo lives in:
https://github.com/SoftwareVerse/userverse-python-client/blob/main/examples/user_demo.py

See the demo README for flags and environment variables:
https://github.com/SoftwareVerse/userverse-python-client/blob/main/examples/user_demo_README.md

## Developing Clients in Other Languages

See the guide for a summary of the Python client architecture and a plan for
implementing SDKs in other languages:
https://github.com/SoftwareVerse/userverse-python-client/blob/main/docs/other-language-clients.md

## Tests

Run the unit tests with:

```bash
pytest
```
