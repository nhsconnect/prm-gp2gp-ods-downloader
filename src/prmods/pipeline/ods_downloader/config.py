import sys
from dataclasses import dataclass, MISSING, fields
import logging
from typing import Optional

from prmods.domain.ods_portal.sources import ODS_PORTAL_SEARCH_URL

logger = logging.getLogger(__name__)


def _read_env(field, env_vars):
    env_var = field.name.upper()
    if env_var in env_vars:
        return env_vars[env_var]
    elif field.default != MISSING:
        return field.default
    else:
        logger.error(f"Expected environment variable {env_var} was not set, exiting...")
        sys.exit(1)


@dataclass
class OdsPortalConfig:
    output_file: str
    mapping_file: str
    search_url: Optional[str] = ODS_PORTAL_SEARCH_URL
    s3_endpoint_url: Optional[str] = None

    @classmethod
    def from_environment_variables(cls, env_vars):
        return cls(**{field.name: _read_env(field, env_vars) for field in fields(cls)})
