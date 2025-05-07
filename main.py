import asyncio
from crawler.crawler import Crawler


async def main():
    keywords = ['agrotech']
    proxies = [

    ]
    proxies = [f'http://{proxy}' for proxy in proxies]
    type_ = 'Repositories'
    crawler = Crawler(keywords, proxies, type_)
    await crawler.crawl()


if __name__ == "__main__":
    asyncio.run(main())
