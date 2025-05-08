import pytest
import asyncio
from unittest.mock import  patch
from aiohttp import ClientSession
from crawler.crawler import Request, Response, Item


@pytest.mark.asyncio
async def test_crawler_initialization(crawler):
    assert crawler.keywords == ["python", "async"]
    assert crawler.proxies == ["proxy1", "proxy2"]
    assert crawler.type == "repositories"
    assert isinstance(crawler.queue, asyncio.Queue)
    assert isinstance(crawler.buffer, list)
    assert len(crawler.buffer) == 0
    assert isinstance(crawler.session, ClientSession)

@pytest.mark.asyncio
async def test_start(crawler):
    await crawler.start()
    assert crawler.queue.qsize() == 2
    url = await crawler.queue.get()
    assert isinstance(url, Request)
    assert "python" in url.url
    url = await crawler.queue.get()
    assert isinstance(url, Request)
    assert "async" in url.url

@pytest.mark.asyncio
async def test_request(crawler, mock_response):
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_get.return_value.__aenter__.return_value = mock_response
        request = Request("https://github.com/search?q=python&type=repositories", lambda x: [])
        response = await crawler.request(request)
        assert isinstance(response, Response)
        assert response.body == "<html>Mock HTML</html>"

@pytest.mark.asyncio
async def test_item_processing(crawler):
    test_item = Item('http://some.url')
    crawler.item(test_item)
    assert len(crawler.buffer) == 1
    assert crawler.buffer[0] == test_item

@pytest.mark.asyncio
async def test_crawl_with_mocked_requests(crawler, mock_response, tmp_path):
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_get.return_value.__aenter__.return_value = mock_response
        test_item = Item('http://some.url')
        crawler.parser.parse_search_page = lambda x: [test_item]
        await crawler.crawl()
        assert len(crawler.buffer) > 0
        assert isinstance(crawler.buffer[0], Item)

@pytest.mark.asyncio
async def test_orchestrate(crawler):
    request = Request("https://github.com/search?q=python&type=repositories", lambda x: [])
    with patch.object(crawler, 'request') as mock_request:
        mock_response = Response("test_url", None, "<html></html>", request)
        mock_request.return_value = mock_response
        await crawler.orchestrate(request)
        mock_request.assert_called_once()
    test_item = Item('http://some.url')
    await crawler.orchestrate(test_item)
    assert test_item in crawler.buffer