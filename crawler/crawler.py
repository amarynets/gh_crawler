import asyncio
from urllib.parse import urljoin, urlparse
import logging
import random
import ssl

import aiohttp

from crawler.parsers.github import GHSearchPageParser
from crawler.core import Response, Request, Item


class ParserTypes:
    repository = 'repositories'
    wikis = 'wikis'
    issues = 'issues'


PARSER_REGISTRY = {
    ParserTypes.repository: GHSearchPageParser
}


class Crawler:
    def __init__(self, keywords: list[str], proxies: list[str], type: str, result_queue):
        self.keywords = keywords
        self.proxies = proxies
        self.proxy = random.choice(self.proxies) if self.proxies else None
        self.type = type.lower()
        # TODO handle unexpected type
        self.parser = PARSER_REGISTRY[self.type]()
        self.queue = asyncio.Queue()
        self.result_queue = result_queue
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initialized crawler with {len(keywords)} keywords and {len(proxies)} proxies")
        self.semaphore = asyncio.Semaphore(5)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self.session = aiohttp.ClientSession(connector=connector)

    async def start(self):
        main_url = 'https://github.com/search'
        for keyword in self.keywords:
            request = Request(main_url, self.parser.parse_search_page, meta={'params': {'q': keyword, 'type': self.type}})
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
            self.logger.info('Crawl queue is empty. Exiting')
            return

    async def request(self, request: Request):
        async with self.semaphore:
                try:
                    params = request.meta.get('params', {})
                    async with self.session.get(request.url, proxy=self.proxy, params=params) as response:
                        html = await response.text()
                        return Response(response.url, response, html, request)
                except Exception as e:
                    self.logger.exception('Exception during request: %s', request.url)
                    return Response(request.url, None, None, request)

    def response(self, response: Response):
        yield from response.request.parse_function(response)

    def item(self, item: Item):
        self.result_queue.put(item)

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

    async def worker(self):
        while True:
            obj = await self.queue.get()
            try:
                if obj is None:
                    break
                await self.orchestrate(obj)
            finally:
                self.queue.task_done()
