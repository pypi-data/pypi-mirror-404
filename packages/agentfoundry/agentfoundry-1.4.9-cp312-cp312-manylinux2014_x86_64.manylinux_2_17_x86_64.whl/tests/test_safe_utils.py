import pytest
import logging
from unittest.mock import MagicMock
from agentfoundry.utils.safe import safe_call

def test_safe_call_success():
    mock_logger = MagicMock(spec=logging.Logger)
    result = safe_call(lambda: "success", mock_logger, "Error: {e}")
    assert result == "success"
    mock_logger.error.assert_not_called()

def test_safe_call_failure():
    mock_logger = MagicMock(spec=logging.Logger)
    
    def fail():
        raise ValueError("Something went wrong")
        
    result = safe_call(fail, mock_logger, "Error occurred: {e}")
    
    assert result is None
    mock_logger.error.assert_called_once()
    args = mock_logger.error.call_args
    assert "Error occurred: Something went wrong" in args[0][0]

def test_safe_call_with_exc_info():
    mock_logger = MagicMock(spec=logging.Logger)
    
    def fail():
        raise ValueError("Fail")
        
    safe_call(fail, mock_logger, "Err", exc_info=True)
    
    mock_logger.error.assert_called_once()
    # Verify exc_info passed as keyword arg
    assert mock_logger.error.call_args[1]["exc_info"] is True
