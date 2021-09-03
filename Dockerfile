FROM python:3.9-slim

COPY . /prmods

RUN cd /prmods && python setup.py install

ENTRYPOINT ["python", "-m", "prmods.pipeline.main"]
