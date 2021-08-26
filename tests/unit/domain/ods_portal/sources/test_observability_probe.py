import pytest

from prmods.domain.ods_portal.metadata_service import MetadataServiceObservabilityProbe


def test_probe_should_raise_warning_given_missing_ods_code():
    probe = MetadataServiceObservabilityProbe()
    with pytest.warns(RuntimeWarning) as warning:
        probe.record_asids_not_found("ABC123")
        assert str(warning[0].message) == "ASIDS not found for ODS code: ABC123"
