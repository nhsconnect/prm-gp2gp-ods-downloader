import logging
from dataclasses import MISSING, dataclass, fields
from datetime import datetime
from typing import Optional

from dateutil.parser import isoparse

from prmods.domain.ods_portal.ods_portal_client import ODS_PORTAL_SEARCH_URL

logger = logging.getLogger(__name__)


class MissingEnvironmentVariable(Exception):
    pass


def _convert_env_value(env_value, config_type):
    if config_type == datetime:
        return isoparse(env_value)
    return env_value


def _read_env(field, env_vars):
    env_var = field.name.upper()
    if env_var in env_vars:
        env_value = env_vars[env_var]
        return _convert_env_value(env_value, field.type)
    elif field.default != MISSING:
        return field.default
    else:
        raise MissingEnvironmentVariable(
            f"Expected environment variable {env_var} was not set, exiting..."
        )


@dataclass
class OdsPortalConfig:
    output_bucket: str
    mapping_bucket: str
    build_tag: str
    date_anchor: datetime
    search_url: Optional[str] = ODS_PORTAL_SEARCH_URL
    s3_endpoint_url: Optional[str] = None

    @classmethod
    def from_environment_variables(cls, env_vars):
        return cls(**{field.name: _read_env(field, env_vars) for field in fields(cls)})
