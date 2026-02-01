"""Tests for the document_reader tool."""

import io
import pytest
from unittest.mock import MagicMock, patch
from agentfoundry.agents.tools.document_reader import ingest_document

class MockFileStorage:
    def __init__(self, data, filename):
        self.data = data
        self.filename = filename
    def read(self):
        return self.data

def test_ingest_plain_text_string():
    text = "Hello   World"
    result = ingest_document(text)
    assert result == "Hello World"

def test_ingest_file_like_text():
    f = MockFileStorage(b"Clean  Content", "test.txt")
    result = ingest_document(f)
    assert result == "Clean Content"

def test_ingest_file_like_pdf():
    # Mock PdfReader
    with patch("agentfoundry.agents.tools.document_reader.PdfReader") as mock_reader:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Page 1 Content"
        mock_reader.return_value.pages = [mock_page]
        
        f = MockFileStorage(b"%PDF-1.4...", "doc.pdf")
        result = ingest_document(f)
        
        assert "Page 1 Content" in result

def test_ingest_url():
    with patch("requests.get") as mock_get:
        mock_get.return_value.text = "Web   Content"
        mock_get.return_value.raise_for_status = MagicMock()
        
        result = ingest_document("http://example.com")
        
        assert result == "Web Content"
        mock_get.assert_called_with("http://example.com")

def test_ingest_local_file(tmp_path):
    # Create a temp file
    p = tmp_path / "local.txt"
    p.write_text("Local   File", encoding="utf-8")
    
    result = ingest_document(str(p))
    assert result == "Local File"
