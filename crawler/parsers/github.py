import logging
from typing import Generator

from bs4 import BeautifulSoup

from crawler.core import Response, Item, Request
from crawler.parsers import BaseParser


logger = logging.getLogger(__name__)

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
        try:
            owner_element = soup.select_one('a[data-hovercard-type="organization"], a[data-hovercard-type="user"]')
            owner = owner_element.text.strip() if owner_element else "Unknown"

            language_stats = {}
            language_section = soup.select_one('div.Layout-sidebar h2:-soup-contains("Languages")')
            if language_section:
                for tag in language_section.parent.select('ul.list-style-none li a'):
                    if tag.select_one('span.color-fg-default.text-bold.mr-1'):
                        try:
                            language = tag.select('span')[0].text
                            percentage = float(tag.select('span')[1].text.strip('%'))
                            language_stats[language] = percentage
                        except (IndexError, ValueError) as e:
                            logger.warning(f"Failed to parse language stats: {e}")

            item.extra = {
                'owner': owner,
                'language_stats': language_stats
            }
            yield item
        except Exception as e:
            logger.exception("Error parsing detail page", response.url)
            raise e



