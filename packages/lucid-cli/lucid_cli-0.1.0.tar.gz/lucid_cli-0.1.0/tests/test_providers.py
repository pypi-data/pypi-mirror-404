import pytest
from lucid_cli.providers import get_provider
from lucid_cli.providers.gcp import GCPProvider
from lucid_cli.providers.aws import AWSProvider
from lucid_cli.providers.azure import AzureProvider

def test_get_provider_valid():
    """Verify that we can retrieve the correct provider instances."""
    assert isinstance(get_provider("gcp", "test-project", "us-central1"), GCPProvider)
    assert isinstance(get_provider("aws", "test-project", "us-central1"), AWSProvider)
    assert isinstance(get_provider("azure", "test-project", "us-central1"), AzureProvider)

def test_get_provider_invalid():
    """Verify that invalid providers raise a ValueError."""
    with pytest.raises(ValueError, match="Unsupported cloud provider: unknown"):
        get_provider("unknown", "test-project", "us-central1")

def test_gcp_provider_init():
    """Verify GCP provider initialization."""
    p = get_provider("gcp", "test-project", "us-central1")
    assert p.project_id == "test-project"
    assert p.region == "us-central1"
