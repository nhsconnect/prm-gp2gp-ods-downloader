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

This pipeline will fetch ODS codes and names of all active GP practices and save to json file.

To run the ODS Portal pipeline you will need to run the docker image. 
This can be done locally by building the image based on the Dockerfile. Or alternatively the image can be pulled from ECR

This is an example of how to build your image locally:

`docker build . -t <tag>`

To pull the image from AWS ECR, you should login to AWS Vault and then pull the image from ECR:

`aws-vault exec <profile-name>`
`docker pull <account-id>.dkr.ecr.eu-west-2.amazonaws.com/registrations/ods-downloader`

To run the pipeline locally:

`docker run -e MAPPING_FILE=<asid_lookup.csv.gz(s3 format)> -e OUTPUT_FILE=<organisation(s3 format)> -e AWS_ACCESS_KEY_ID=<AWS_ACCESS_KEY_ID> -e AWS_SECRET_ACCESS_KEY=<AWS_SECRET_ACCESS_KEY> -e AWS_SESSION_TOKEN=<AWS_SESSION_TOKEN> -e AWS_SECURITY_TOKEN=<AWS_SECURITY_TOKEN> <image-name>:<image-tag>
 `

## Troubleshooting

```
ERROR: InvocationError for command /YOUR_PROJECT_DIRECTORY/prm-gp2gp-ods-downloader/.tox/check-format/bin/black --check -t py38 -l100 src/ tests/ setup.py (exited with code 2)
```

If you see this error, you need to delete the .tox package and try again
