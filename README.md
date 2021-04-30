# prm-gp2gp-ods-downloader

This repository contains the pipeline responsible for fetching ODS codes and names of all active GP practices and saving it to json file.

<!-- ## Running

### Extracting Spine data from NMS

Run the following query for the desired time range and save the results as a csv.

```
index="spine2vfmmonitor" service="gp2gp" logReference="MPS0053d"
| table _time, conversationID, GUID, interactionID, messageSender, messageRecipient, messageRef, jdiEvent, toSystem, fromSystem
``` -->

## Developing

Common development workflows are defined in the `tasks` script.

These generally work by running a command in a virtual environment configured via `tox.ini`.

### Prerequisites

- Python 3.9
- [Tox](https://tox.readthedocs.io/en/latest/#) `brew install tox`
- [Docker](https://www.docker.com/get-started)

###Setup###
These instructions assume you are using:

- [aws-vault](https://github.com/99designs/aws-vault) to validate your AWS credentials.

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

### ODS Portal Pipeline

This pipeline will fetch ODS codes and names of all active GP practices and save the JSON file to an S3 bucket.

To build your image locally:

`docker build . -t <tag>`

## Troubleshooting

```
ERROR: InvocationError for command /YOUR_PROJECT_DIRECTORY/prm-gp2gp-ods-download/.tox/check-format/bin/black --check -t py38 -l100 src/ tests/ setup.py (exited with code 2)
```

If you see this error, you need to delete the .tox package and try again.
