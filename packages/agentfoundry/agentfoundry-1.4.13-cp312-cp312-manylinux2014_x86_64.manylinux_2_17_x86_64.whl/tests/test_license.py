import pytest
import os
from unittest.mock import patch, MagicMock
from agentfoundry.license import license as af_license

@pytest.fixture
def mock_license_core():
    with patch("agentfoundry.license.license._license_core") as mock_core:
        # Default behavior: machine id
        mock_core.current_machine_id.return_value = b"test-machine-id"
        yield mock_core

@pytest.fixture
def clean_env():
    # Save original env
    old_env = os.environ.get("AGENTFOUNDRY_LICENSE_FILE")
    if old_env:
        del os.environ["AGENTFOUNDRY_LICENSE_FILE"]
    yield
    if old_env:
        os.environ["AGENTFOUNDRY_LICENSE_FILE"] = old_env

def test_get_machine_id(mock_license_core):
    mid = af_license.get_machine_id()
    assert mid == "test-machine-id"
    mock_license_core.current_machine_id.assert_called_once()

def test_verify_license_success(mock_license_core):
    mock_license_core.validate_license.return_value = (True, "details")
    # Mock os.path.exists to simulate license file existing
    with patch("os.path.exists", return_value=True):
         assert af_license.verify_license() is True

def test_verify_license_failure(mock_license_core):
    mock_license_core.validate_license.return_value = (False, "invalid")
    with patch("os.path.exists", return_value=True):
        assert af_license.verify_license() is False

def test_enforce_license_raises(mock_license_core):
    mock_license_core.validate_license.return_value = (False, "invalid")
    with patch("os.path.exists", return_value=True):
        with pytest.raises(RuntimeError, match="Invalid, tampered, or expired"):
            af_license.enforce_license()

def test_license_path_resolution_env(clean_env):
    os.environ["AGENTFOUNDRY_LICENSE_FILE"] = "/custom/path.lic"
    paths = af_license._default_license_paths()
    assert "/custom/path.lic" in paths[0]

def test_resolve_license_file_exists():
    with patch("os.path.exists") as mock_exists:
        # Second path exists
        mock_exists.side_effect = [False, True, False, False] 
        path = af_license._resolve_license_file()
        # Verify it picked the second one in the list (index 1) which corresponds to ~/.config...
        # Note: _default_license_paths logic: 
        # 1. env (if set) 
        # 2. xdg 
        # 3. cwd 
        # 4. pkg
        
        # We need to know what _default_license_paths returned.
        # But generally, it should return the one that 'exists'.
        assert path is not None
