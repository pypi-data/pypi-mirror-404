# DAQview

DAQview is a desktop application for viewing live and historic DAQ data
from the Airborne Engineering Ltd DAQ system.

For more information and the user manual, refer to our website:

https://www.ael.co.uk/pages/daqview.html

Licensed under the GPL 3.0 license.

## Installation

The recommended installation method is to use [`uv`](https://docs.astral.sh/uv)
to install the latest published version on PyPI:

```
uv tool install daqview
```

To run DAQview after installation, run `daqview`.

On a Linux desktop, complete installation by running `daqview --install`
to add the application to your list of locally-installed applications.

To upgrade to a newer release of DAQview, run `uv tool upgrade daqview`.

DAQview can also be installed using `pipx` or other tools for installing Python
applications, e.g. `pipx install daqview`.

## Development Environment

Run from a local copy of the code using:
```
uv run daqview
```

Run tests with:
```
uv run pytest
```
