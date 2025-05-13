import asyncio
from queue import Queue

from crawler.crawler import Crawler


import json
import sys
import logging


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s:%(name)s:%(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    # TODO Add validation
    input_data = json.load(sys.stdin)
    keywords = input_data.get("keywords", [])
    proxies = input_data.get("proxies", [])
    type_ = input_data.get("type", "Repositories")

    if not keywords:
        logger.warning("No keywords provided. Crawling won't yield results.")
        return

    logger.info('Starting crawler with keywords: %s', keywords)
    logger.info('Using type: %s', type_)
    logger.info('Using %s proxies', len(proxies))

    proxies = [f"http://{proxy}" if not proxy.startswith('http') else proxy for proxy in proxies]
    queue = Queue()
    crawler = Crawler(keywords, proxies, type_, queue)
    await crawler.crawl()
    with open("output.json", "w") as f:
        while not queue.empty():
            f.write(json.dumps(queue.get().serialize()) + "\n")
            queue.task_done()
    queue.join()


if __name__ == "__main__":
    asyncio.run(main())
