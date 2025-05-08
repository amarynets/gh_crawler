import pytest
from bs4 import BeautifulSoup
from unittest.mock import MagicMock, patch

from crawler.parsers.github import GHSearchPageParser
from crawler.core import Response, Request, Item



@pytest.fixture
def parser():
    return GHSearchPageParser()

@pytest.fixture
def search_page_html():
    return """
    <!DOCTYPE html>
    <html>
    <body>
        <div data-testid="results-list">
            <div class="search-result-item">
                <div class="search-title">
                    <a href="/user1/repo1">user1/repo1</a>
                </div>
            </div>
            <div class="search-result-item">
                <div class="search-title">
                    <a href="/user2/repo2">user2/repo2</a>
                </div>
            </div>
            <div class="search-result-item">
                <div class="search-title">
                    <a href="/user3/repo3">user3/repo3</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@pytest.fixture
def detail_page_html():
    return """
    <!DOCTYPE html>
    <html>
    <body>
        <a data-hovercard-type="organization">organization-name</a>
        <div class="Layout-sidebar">
            <h2>Languages</h2>
            <ul class="list-style-none">
                <li>
                    <a>
                        <span class="color-fg-default text-bold mr-1">Python</span>
                        <span>80.5%</span>
                    </a>
                </li>
                <li>
                    <a>
                        <span class="color-fg-default text-bold mr-1">JavaScript</span>
                        <span>19.5%</span>
                    </a>
                </li>
            </ul>
        </div>
    </body>
    </html>
    """

@pytest.fixture
def search_response(search_page_html):
    mock_response = MagicMock()
    mock_response.url = "https://github.com/search?q=python&type=repositories"

    mock_request = MagicMock()

    return Response(
        url="https://github.com/search?q=python&type=repositories",
        response=mock_response,
        body=search_page_html,
        request=mock_request
    )

@pytest.fixture
def detail_response(detail_page_html):
    mock_response = MagicMock()
    mock_response.url = "https://github.com/user1/repo1"

    test_item = Item(url="https://github.com/user1/repo1")

    mock_request = MagicMock()
    mock_request.meta = {'item': test_item}

    return Response(
        url="https://github.com/user1/repo1",
        response=mock_response,
        body=detail_page_html,
        request=mock_request
    )

def test_parse_search_page(parser, search_response):
    # Test parsing search results
    results = list(parser.parse_search_page(search_response))

    # Should generate 3 requests for detail pages
    assert len(results) == 3

    # Verify all results are Request objects
    for result in results:
        assert isinstance(result, Request)
        assert result.parse_function == parser.parse_detail_page
        assert 'item' in result.meta
        assert isinstance(result.meta['item'], Item)

    # Check URLs of generated requests
    assert "user1/repo1" in results[0].url
    assert "user2/repo2" in results[1].url
    assert "user3/repo3" in results[2].url

def test_search_page_with_empty_results(parser):
    # Test with empty search results
    empty_html = """
    <!DOCTYPE html>
    <html>
    <body>
        <div data-testid="results-list">
            <!-- No search results -->
        </div>
    </body>
    </html>
    """

    mock_response = MagicMock()
    mock_response.url = "https://github.com/search?q=nonexistent&type=repositories"

    mock_request = MagicMock()

    response = Response(
        url="https://github.com/search?q=nonexistent&type=repositories",
        response=mock_response,
        body=empty_html,
        request=mock_request
    )

    results = list(parser.parse_search_page(response))

    # Should generate no requests
    assert len(results) == 0

def test_parse_detail_page(parser, detail_response):
    # Test parsing repository detail page
    results = list(parser.parse_detail_page(detail_response))

    # Should yield one item
    assert len(results) == 1
    assert isinstance(results[0], Item)

    # Verify extracted information
    item = results[0]
    assert item.url == "https://github.com/user1/repo1"
    assert item.extra is not None
    assert item.extra['owner'] == "organization-name"

    # Check language stats
    assert 'language_stats' in item.extra
    assert len(item.extra['language_stats']) == 2
    assert item.extra['language_stats']['Python'] == 80.5
    assert item.extra['language_stats']['JavaScript'] == 19.5

def test_detail_page_missing_elements(parser):
    # Test with missing elements in detail page
    empty_html = """
    <!DOCTYPE html>
    <html>
    <body>
        <!-- Missing organization and languages -->
    </body>
    </html>
    """

    mock_response = MagicMock()
    mock_response.url = "https://github.com/user1/repo1"

    test_item = Item(url="https://github.com/user1/repo1")

    mock_request = MagicMock()
    mock_request.meta = {'item': test_item}

    response = Response(
        url="https://github.com/user1/repo1",
        response=mock_response,
        body=empty_html,
        request=mock_request
    )

    # Should raise an exception due to missing elements
    with pytest.raises(AttributeError):
        list(parser.parse_detail_page(response))

def test_urljoin_functionality(parser, search_response):
    # Override the HTML to test urljoin with relative URLs
    search_response.body = """
    <!DOCTYPE html>
    <html>
    <body>
        <div data-testid="results-list">
            <div class="search-title">
                <a href="/relative/path">relative path</a>
            </div>
        </div>
    </body>
    </html>
    """

    # Mock the urljoin method to verify it's called correctly
    with patch.object(search_response, 'urljoin') as mock_urljoin:
        mock_urljoin.return_value = "https://github.com/relative/path"

        results = list(parser.parse_search_page(search_response))

        assert len(results) == 1
        mock_urljoin.assert_called_once_with("/relative/path")
        assert results[0].url == "https://github.com/relative/path"
