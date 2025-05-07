import asyncio
import json
import logging

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
        # TODO handle unexpected type
        self.parser = PARSER_REGISTRY[self.type]()
        self.queue = asyncio.Queue()
        self.buffer = []
        self.logger = logger
        self.logger.info(f"Initialized crawler with {len(keywords)} keywords and {len(proxies)} proxies")
        self.semaphore = asyncio.Semaphore(5)
        self.session = aiohttp.ClientSession()


    async def start(self):
        urls = [
            f'https://github.com/search?q={keyword}&type={self.type}'
            for keyword in self.keywords
        ]
        for url in urls:
            request = Request(url, self.parser.parse_search_page)
            await self.queue.put(request)

    async def orchestrate(self, obj):
        # TODO Make async
        if isinstance(obj, Request):
            self.logger.info('Send request to %s', obj.url)
            response = await self.request(obj)
            await self.queue.put(response)
        elif isinstance(obj, Response):
            self.logger.info('Get response from %s', obj.request.url)
            for obj in self.response(obj):
                await self.queue.put(obj)
        elif isinstance(obj, Item):
            self.logger.info('Item: %s', obj)
            self.item(obj)
        else:
            raise

    async def request(self, request: Request):
        async with self.semaphore:
            async with self.session.get(request.url) as response:
                html = await response.text()
                return Response(response.url, response, html, request)

    def response(self, response: Response):
        yield from response.request.parse_function(response)

    def item(self, item: Item):
        self.buffer.append(item)

    async def crawl(self):
        self.logger.info('Start crawler')

        await self.start()
        worker_count = 5
        workers = [asyncio.create_task(self.worker()) for _ in range(worker_count)]

        await self.queue.join()

        for _ in range(worker_count):
            await self.queue.put(None)

        await asyncio.gather(*workers, return_exceptions=True)
        await self.session.close()
        result = [item.serialize() for item in self.buffer]
        with open('output.json', 'w') as f:
            json.dump(result, f, indent=2)

    async def worker(self):
        while True:
            obj = await self.queue.get()
            try:
                await self.orchestrate(obj)
            finally:
                self.queue.task_done()
