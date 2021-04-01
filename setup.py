from setuptools import find_packages, setup

setup(
    name="gp2gp-ods-downloader",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "python-dateutil~=2.8",
        "requests~=2.2",
        "boto3~=1.17.42",
    ],
    entry_points={
        "console_scripts": [
            "ods-portal-pipeline=prmods.pipeline.ods_downloader.main:main",
        ]
    },
)
