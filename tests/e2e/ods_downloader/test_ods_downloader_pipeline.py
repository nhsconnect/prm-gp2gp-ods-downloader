import gzip
import os
import shutil
import boto3

from os import environ
from threading import Thread
from botocore.config import Config
from moto.server import DomainDispatcherApplication, create_backend_app
from werkzeug.serving import make_server

from prmods.pipeline.ods_downloader.config import OdsPortalConfig
from prmods.pipeline.ods_downloader.main import main


class ThreadedServer:
    def __init__(self, server):
        self._server = server
        self._thread = Thread(target=server.serve_forever)

    def start(self):
        self._thread.start()

    def stop(self):
        self._server.shutdown()
        self._thread.join()


def _build_fake_s3(host, port):
    app = DomainDispatcherApplication(create_backend_app, "s3")
    server = make_server(host, port, app)
    return ThreadedServer(server)


def gzip_file(input_file_path):
    gzip_file_path = input_file_path.with_suffix(".gz")
    with open(input_file_path, "rb") as input_file:
        with gzip.open(gzip_file_path, "wb") as output_file:
            shutil.copyfileobj(input_file, output_file)
    return gzip_file_path


def test_with_s3_output(datadir):
    fake_s3_host = "127.0.0.1"
    fake_s3_port = 8887
    fake_s3_url = f"http://{fake_s3_host}:{fake_s3_port}"
    fake_s3_access_key = "testing"
    fake_s3_secret_key = "testing"
    fake_s3_region = "us-west-1"

    fake_s3 = _build_fake_s3(fake_s3_host, fake_s3_port)
    fake_s3.start()

    s3 = boto3.resource(
        "s3",
        endpoint_url=fake_s3_url,
        aws_access_key_id=fake_s3_access_key,
        aws_secret_access_key=fake_s3_secret_key,
        config=Config(signature_version="s3v4"),
        region_name=fake_s3_region,
    )

    output_bucket_name = "prm-gp2gp-ods-data"
    output_bucket = s3.Bucket(output_bucket_name)
    output_bucket.create()

    input_mapping_file = gzip_file(datadir / "asid_mapping.csv")

    output_bucket.upload_file(input_mapping_file.__str__(), "asidLookup.csv.gz")

    environ["AWS_ACCESS_KEY_ID"] = "testing"
    environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    environ["AWS_DEFAULT_REGION"] = "us-west-1"

    main(
        OdsPortalConfig(
            output_file="s3://prm-gp2gp-ods-data/output.json",
            mapping_file="s3://prm-gp2gp-ods-data/asidLookup.csv.gz",
            s3_endpoint_url=fake_s3_url,
        )
    )

    output_bucket.download_file("output.json", "output.json")

    output_file_content = open("output.json").read()

    try:
        assert "practices" in output_file_content
        assert "ccg" in output_file_content
    finally:
        output_bucket.objects.all().delete()
        output_bucket.delete()
        fake_s3.stop()
        os.remove("output.json")
