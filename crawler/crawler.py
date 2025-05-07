import json
import random
import logging
from collections import deque

import aiohttp

from crawler.parsers.github import GHSearchPageParser
from crawler.core import Response, Request, Item

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)



class ParserTypes:
    repository = 'repositories'
    wikis = 'wikis'
    issues = 'issues'


PARSER_REGISTRY = {
    ParserTypes.repository: GHSearchPageParser
}


class Crawler:
    def __init__(self, keywords: list[str], proxies: list[str], type: str):
        self.keywords = keywords
        self.proxies = proxies
        self.type = type.lower()
        self.parser = PARSER_REGISTRY[self.type]()
        self.queue = deque()
        self.buffer = []
        self.logger = logger


    def start(self):
        urls = [
            f'https://github.com/search?q={keyword}&type={self.type}'
            for keyword in self.keywords
        ]
        for url in urls:
            request = Request(url, self.parser.parse_search_page)
            self.queue.append(request)

    async def orchestrate(self, obj):
        if isinstance(obj, Request):
            self.logger.info('Send request to %s', obj.url)
            response = await self.request(obj)
            self.queue.append(response)
        elif isinstance(obj, Response):
            self.logger.info('Get response from %s', obj.request.url)
            for obj in self.response(obj):
                self.queue.append(obj)
        elif isinstance(obj, Item):
            self.logger.info('Item: %s', obj)
            self.item(obj)
        else:
            raise

    async def request(self, request: Request):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    request.url,
                    # proxy=random.choice(self.proxies)
            ) as response:
                html = await response.text()
                resp = Response(response.url, response, html, request)
                return resp

    def response(self, response: Response):
        yield from response.request.parse_function(response)

    def item(self, item: Item):
        self.buffer.append(item)

    async def crawl(self):
        self.logger.info('Start crawler')
        self.start()
        while self.queue:
            obj = self.queue.popleft()
            await self.orchestrate(obj)
        print(self.buffer)
