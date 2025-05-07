import asyncio
from crawler.crawler import Crawler


import json
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    input_data = {} #json.load(sys.stdin)
    keywords = input_data.get("keywords", ['drone'])
    proxies = input_data.get("proxies", [])
    type_ = input_data.get("type", "Repositories")

    if not keywords:
        logger.warning("No keywords provided. Crawling won't yield results.")
        return

    logger.info(f"Starting crawler with keywords: {keywords}")
    logger.info(f"Using type: {type_}")
    logger.info(f"Using {len(proxies)} proxies")

    # Format proxies
    proxies = [f"http://{proxy}" if not proxy.startswith('http') else proxy for proxy in proxies]

    # Initialize and run crawler
    crawler = Crawler(keywords, proxies, type_)
    await crawler.crawl()


if __name__ == "__main__":
    asyncio.run(main())
