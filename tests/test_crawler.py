import pytest
import asyncio
from unittest.mock import  patch
from aiohttp import ClientSession
from crawler.crawler import Request, Response, Item


import asyncio
import json
import os
from unittest.mock import patch, MagicMock

import pytest
from aiohttp import ClientSession
from crawler.core import Request, Response, Item


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
async def test_request_method(crawler, mock_response):
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_get.return_value.__aenter__.return_value = mock_response
        request = Request("https://github.com/search?q=python&type=repositories", lambda x: [])
        response = await crawler.request(request)
        assert isinstance(response, Response)
        assert response.body == "<html>Mock HTML</html>"


@pytest.mark.asyncio
async def test_request_with_proxy(crawler, mock_response):
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_get.return_value.__aenter__.return_value = mock_response
        with patch('random.choice', return_value="proxy1") as mock_choice:
            request = Request("https://github.com/search?q=python&type=repositories", lambda x: [])
            response = await crawler.request(request)
            assert isinstance(response, Response)
            mock_get.assert_called_once()
            # Verify proxy was used
            call_kwargs = mock_get.call_args.kwargs
            assert 'proxy' in call_kwargs
            assert call_kwargs['proxy'] == 'proxy1'


@pytest.mark.asyncio
async def test_item_processing(crawler):
    test_item = Item('http://some.url')
    crawler.item(test_item)
    assert len(crawler.buffer) == 1
    assert crawler.buffer[0] == test_item


@pytest.mark.asyncio
async def test_response_processing(crawler):
    mock_parser = MagicMock()
    mock_parser.return_value = [Item('http://result1.url'), Item('http://result2.url')]
    
    request = Request('http://test.url', mock_parser)
    response = Response('http://test.url', None, "<html>content</html>", request)
    
    results = list(crawler.response(response))
    assert len(results) == 2
    assert all(isinstance(item, Item) for item in results)
    mock_parser.assert_called_once_with(response)


@pytest.mark.asyncio
async def test_crawl_with_mocked_requests(crawler, mock_response, tmp_path):
    # Override output location for test
    output_file = os.path.join(tmp_path, "output.json")
    
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_get.return_value.__aenter__.return_value = mock_response
        
        # Mock parser to return a test item
        test_item = Item('http://some.url')
        test_item.extra = {"test": "data"}
        
        with patch.object(crawler.parser, 'parse_search_page', return_value=[test_item]):
            # Mock output file location
            with patch('builtins.open', create=True) as mock_open:
                mock_file = MagicMock()
                mock_open.return_value.__enter__.return_value = mock_file
                
                await crawler.crawl()
                
                # Check that buffer contains our item
                assert len(crawler.buffer) == 1
                
                # Check that json.dump was called to write results
                mock_calls = [call for call in mock_file.mock_calls if 'json.dump' in str(call)]
                assert len(mock_calls) > 0


from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_start_method(crawler):
    with patch.object(crawler, 'queue') as mock_queue:
        # Make the queue.put method return an awaitable
        mock_queue.put = AsyncMock()
        
        await crawler.start()
        
        # Should add requests for each keyword
        assert mock_queue.put.call_count == 2
        
        # Check that requests were created properly
        calls = mock_queue.put.call_args_list
        for i, call in enumerate(calls):
            request = call[0][0]
            assert isinstance(request, Request)
            assert crawler.keywords[i] in request.url
            assert "repositories" in request.url


@pytest.mark.asyncio
async def test_orchestrate_with_request(crawler, mock_response):
    with patch.object(crawler, 'request') as mock_request:
        with patch.object(crawler, 'queue') as mock_queue:
            test_request = Request('http://test.url', lambda x: [])
            test_response = Response('http://test.url', None, "<html>content</html>", test_request)
            
            # Make the mocked methods return awaitable objects
            mock_request.return_value = test_response
            mock_request.__await__ = lambda self: asyncio.Future().__await__()
            mock_queue.put = AsyncMock()
            
            await crawler.orchestrate(test_request)
            
            # Verify request was called
            mock_request.assert_called_once_with(test_request)
            
            # Verify response was added to queue
            mock_queue.put.assert_called_once()
            args = mock_queue.put.call_args[0]
            assert isinstance(args[0], Response)


@pytest.mark.asyncio
async def test_orchestrate_with_response(crawler):
    with patch.object(crawler, 'response') as mock_response_method:
        with patch.object(crawler, 'queue') as mock_queue:
            test_request = Request('http://test.url', lambda x: [])
            test_response = Response('http://test.url', None, "<html>content</html>", test_request)
            
            # Mock response method to return items
            result_items = [Item('http://result1.url'), Item('http://result2.url')]
            mock_response_method.return_value = result_items
            
            # Make queue.put an AsyncMock
            mock_queue.put = AsyncMock()
            
            await crawler.orchestrate(test_response)
            
            # Verify response method was called
            mock_response_method.assert_called_once_with(test_response)
            
            # Verify items were added to queue
            assert mock_queue.put.call_count == 2
            for i, call in enumerate(mock_queue.put.call_args_list):
                assert call[0][0] == result_items[i]


@pytest.mark.asyncio
async def test_orchestrate_with_item(crawler):
    with patch.object(crawler, 'item') as mock_item_method:
        test_item = Item('http://test.url')
        
        await crawler.orchestrate(test_item)
        
        # Verify item method was called with the item
        mock_item_method.assert_called_once_with(test_item)

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