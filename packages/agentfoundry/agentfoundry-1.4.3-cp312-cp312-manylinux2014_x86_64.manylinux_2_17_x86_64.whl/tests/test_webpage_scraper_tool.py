import logging
import pytest
import json

from agentfoundry.agents.tools.webpage_scraper_tool import scrape_webpage

# Replace with your actual LinkedIn profile URL or set via env var if desired.
PROFILE_URL = "https://www.linkedin.com/in/syntheticore/"


def test_scrape_linkedin_profile(caplog):
    """Test scraping a LinkedIn profile page and verify structured JSON output."""
    caplog.set_level(logging.DEBUG)

    # Try JS-enabled scrape for dynamic content (LinkedIn profile requires JS)
    result = scrape_webpage(url=PROFILE_URL, render_js=True)
    print(json.dumps(result, indent=2))

    # If network or JS rendering failed, skip rather than fail the test
    if "error" in result:
        pytest.skip(f"Could not scrape LinkedIn profile: {result['error']}")

    # Basic structural assertions on successful scrape
    assert isinstance(result, dict)
    assert result.get("url") == PROFILE_URL
    assert "title" in result and result["title"] is not None
    assert "headings" in result and isinstance(result["headings"], list)
    # Paragraphs, links, images, lists, and tables should be present
    for field in ("paragraphs", "links", "images", "lists", "tables"):
        assert field in result and isinstance(result[field], list)


def test_scrape_invalid_url(caplog):
    """Test scraping an invalid URL returns an error structure."""
    caplog.set_level(logging.DEBUG)
    bad_url = "https://invalid.url.test/404"

    result = scrape_webpage(url=bad_url, timeout=2)

    # Expect an error key for unreachable URL
    assert isinstance(result, dict)
    assert "error" in result