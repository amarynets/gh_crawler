# At the top of your test file
from unittest.mock import Mock

import pytest
import pytest_asyncio

from crawler.crawler import Crawler

pytest_plugins = ["pytest_asyncio"]

@pytest_asyncio.fixture
async def crawler():
    keywords = ["python", "async"]
    proxies = ["proxy1", "proxy2"]
    crawler_instance = Crawler(keywords=keywords, proxies=proxies, type="repositories")
    yield crawler_instance
    await crawler_instance.session.close()


@pytest.fixture
def mock_response():
    async def mock_text():
        return "<html>Mock HTML</html>"

    response = Mock()
    response.text = mock_text
    response.url = "https://github.com/search?q=python&type=repositories"
    return response
