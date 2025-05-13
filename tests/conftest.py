# At the top of your test file
from queue import Queue
from unittest.mock import Mock

import pytest
import pytest_asyncio

from crawler.crawler import Crawler

pytest_plugins = ["pytest_asyncio"]

import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock

from crawler.crawler import Crawler
from crawler.core import Response


@pytest_asyncio.fixture
async def crawler():
    keywords = ["python", "async"]
    proxies = ["proxy1", "proxy2"]
    queue = Queue()
    crawler_instance = Crawler(keywords=keywords, proxies=proxies, type_="repositories", result_queue=queue)
    yield crawler_instance
    await crawler_instance.session.close()


@pytest.fixture
def mock_response():
    response = MagicMock()
    response.text = AsyncMock(return_value="<html>Mock HTML</html>")
    response.url = "https://github.com/search?q=python&type=repositories"
    response.body = "<html>Mock HTML</html>"
    return response


@pytest.fixture
def mock_response():
    async def mock_text():
        return "<html>Mock HTML</html>"

    response = Mock()
    response.text = mock_text
    response.url = "https://github.com/search?q=python&type=repositories"
    return response
