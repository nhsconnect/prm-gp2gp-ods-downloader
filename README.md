# prm-gp2gp-ods-downloader

This repository contains the pipeline responsible for fetching ODS codes and names of all active GP practices and saving it to json file.

## Developing

Common development workflows are defined in the `tasks` script.

### Prerequisites

- Python 3.9. Use [pyenv](https://github.com/pyenv/pyenv) to easily switch Python versions.
- [Pipenv](https://pypi.org/project/pipenv/). Install by running `python -m pip install pipenv`
- [Docker](https://www.docker.com/get-started)

### Setup
These instructions assume you are using:

- [aws-vault](https://github.com/99designs/aws-vault) to validate your AWS credentials.

Run `./tasks devenv` to install required dependencies.

### Running the unit tests

`./tasks test`

### Running the end to end tests

`./tasks e2e-test`

### Running tests, linting, and type checking

`./tasks validate`

### Running tests, linting, and type checking in a docker container

This will run the validation commands in the same container used by the GoCD pipeline.

`./tasks dojo-validate`

### Auto Formatting

`./tasks format`

### Dependency Scanning

`./tasks check-deps`
- If this fails when running outside of Dojo, see [troubleshooting section](### Troubleshooting)

### ODS Portal Pipeline

This pipeline will fetch ODS codes and names of all active GP practices and save the JSON file to an S3 bucket.

To build your image locally:

`docker build . -t <tag>`

### Troubleshooting

#### Checking dependencies fails locally due to pip

If running `./tasks check-deps` fails due to an outdated version of pip, yet works when running it in dojo (i.e. `./tasks dojo-deps`), then the local python environment containing pipenv may need to be updated (using pyenv instead of brew - to better control the pip version).
Ensure you have pyenv installed (use `brew install pyenv`).
Perform the following steps:

1. Run `brew uninstall pipenv`
4. Run `pyenv install <required-python-version>`
5. Run `pyenv global <required-python-version>`
6. Run `python -m pip install pipenv` to install pipenv using the updated python environment.
7. Run `python -m pip install -U "pip>=<required-pip-version>"`
8. Now running `./tasks check-deps` should pass.
    - `pyenv global` should output the specific python version specified rather than `system`.
    - Both `python --version` and `pip --version` should point to the versions you have specified.
    - `ls -l $(which pipenv)` should output `.../.pyenv/shims/pipenv` rather than `...Cellar...` (which is a brew install).
