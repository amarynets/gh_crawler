from typing import Any, Generator

from bs4 import BeautifulSoup

from crawler.core import Response, Item, Request
from crawler.parsers import BaseParser


class GHSearchPageParser(BaseParser):

    def parse_search_page(self, response: Response) -> Generator[Request, None]:
        soup = BeautifulSoup(response.body, features="html.parser")
        links = soup.select('div[data-testid="results-list"] div.search-title a')
        for link in links:
            url = response.urljoin(link.get('href'))
            item = Item(url=url)
            detail_page_request = Request(
                url=item.url,
                parse_function=self.parse_detail_page,
                meta={'item': item}
            )
            yield detail_page_request

    def parse_detail_page(self, response) -> Generator[Item, None]:
        item = response.meta['item']
        soup = BeautifulSoup(response.body, features="html.parser")
        item.extra = {
            'owner': soup.select_one('a[data-hovercard-type="organization"]').text.strip(),
            'language_stats': {
                tag.select('span')[0].text: float(tag.select('span')[1].text.strip('%'))
                for tag in soup.select_one('div.Layout-sidebar h2:-soup-contains("Languages")').parent.select('ul.list-style-none li a') if tag.select_one('span.color-fg-default.text-bold.mr-1')
            }
        }
        yield item
