import os
import pytest
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from lucid_cli.main import app
from lucid_schemas import (
    LUCID_LABEL_AUDITOR,
    LUCID_LABEL_SCHEMA_VERSION,
    LUCID_LABEL_PHASE,
    LUCID_LABEL_INTERFACES
)

runner = CliRunner()

@pytest.fixture
def mock_docker():
    with patch("lucid_cli.auditor.docker.from_env") as mock:
        yield mock

@pytest.fixture
def mock_httpx():
    with patch("httpx.Client") as mock:
        yield mock

def test_verify_image_not_found(mock_docker):
    mock_client = mock_docker.return_value
    mock_client.images.get.side_effect = Exception("No such image")
    
    result = runner.invoke(app, ["auditor", "verify", "non-existent-image"])
    
    assert result.exit_code == 1
    assert "Error inspecting image" in result.stdout

def test_verify_missing_labels(mock_docker):
    mock_client = mock_docker.return_value
    mock_image = MagicMock()
    mock_image.labels = {} # Empty labels
    mock_client.images.get.return_value = mock_image
    
    result = runner.invoke(app, ["auditor", "verify", "bad-image"])
    
    assert result.exit_code == 1
    assert "Missing required label" in result.stdout

def test_verify_success(mock_docker, mock_httpx):
    mock_client = mock_docker.return_value
    
    # Mock Image
    mock_image = MagicMock()
    mock_image.labels = {
        LUCID_LABEL_AUDITOR: "true",
        LUCID_LABEL_SCHEMA_VERSION: "v1.0",
        LUCID_LABEL_PHASE: "input_gate",
        LUCID_LABEL_INTERFACES: "http:8080"
    }
    mock_client.images.get.return_value = mock_image
    
    # Mock Container
    mock_container = MagicMock()
    mock_container.ports = {'8080/tcp': [{'HostIp': '0.0.0.0', 'HostPort': '12345'}]}
    mock_client.containers.run.return_value = mock_container
    
    # Mock HTTPX
    mock_client_instance = mock_httpx.return_value.__enter__.return_value
    mock_client_instance.get.return_value.status_code = 200
    mock_client_instance.post.return_value.status_code = 200
    
    result = runner.invoke(app, ["auditor", "verify", "good-image"])
    
    assert result.exit_code == 0
    assert "Verification complete. Auditor is compliant." in result.stdout
    mock_client.containers.run.assert_called_once()

def test_verify_health_timeout(mock_docker, mock_httpx):
    mock_client = mock_docker.return_value
    mock_image = MagicMock()
    mock_image.labels = {
        LUCID_LABEL_AUDITOR: "true",
        LUCID_LABEL_SCHEMA_VERSION: "v1.0",
        LUCID_LABEL_PHASE: "input_gate"
    }
    mock_client.images.get.return_value = mock_image
    
    mock_container = MagicMock()
    mock_container.ports = {'8080/tcp': [{'HostIp': '0.0.0.0', 'HostPort': '12345'}]}
    mock_client.containers.run.return_value = mock_container
    
    # Mock HTTPX to always fail health check
    mock_client_instance = mock_httpx.return_value.__enter__.return_value
    mock_client_instance.get.side_effect = Exception("Connection refused")
    
    # Speed up test by patching time.sleep
    with patch("time.sleep"):
        result = runner.invoke(app, ["auditor", "verify", "slow-image"])
    
    assert result.exit_code == 1
    assert "Auditor did not become healthy within 10 seconds" in result.stdout

def test_publish_flow(mock_docker, mock_httpx):
    """Test auditor publish flow with HMAC-based signing."""
    mock_client = mock_docker.return_value

    # Setup verify mock
    mock_image = MagicMock()
    mock_image.labels = {
        LUCID_LABEL_AUDITOR: "true",
        LUCID_LABEL_SCHEMA_VERSION: "v1.0",
        LUCID_LABEL_PHASE: "input_gate"
    }
    mock_image.attrs = {'Id': 'sha256:1234567890abcdef'}
    mock_client.images.get.return_value = mock_image

    mock_container = MagicMock()
    mock_container.ports = {'8080/tcp': [{'HostIp': '0.0.0.0', 'HostPort': '12345'}]}
    mock_client.containers.run.return_value = mock_container

    mock_client_instance = mock_httpx.return_value.__enter__.return_value
    mock_client_instance.get.return_value.status_code = 200
    mock_client_instance.post.return_value.status_code = 200

    with patch.dict(os.environ, {"LUCID_API_KEY": "lucid_sk_test"}, clear=False):
        result = runner.invoke(app, ["auditor", "publish", "my-auditor:v1"])

    assert result.exit_code == 0
    assert "Signing digest" in result.stdout
    assert "Auditor notarized successfully!" in result.stdout
    assert "Registering notarization with Lucid Verifier" in result.stdout

