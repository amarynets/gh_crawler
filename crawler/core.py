from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from typing import Optional


class Request:
    def __init__(self, url, parse_function, meta=None):
        self.url = url
        self.parse_function = parse_function
        self.meta = meta if meta else {}

class Response:
    def __init__(self, url, response, body, request):
        self.url = url
        self.response = response
        self.body = body
        self.request = request
        self.meta = self.request.meta

    def urljoin(self, url):
        return urljoin(str(self.response.url), url)



@dataclass
class Item:
    url: str
    extra: Optional[dict] = None

    def serialize(self):
        return {'url': self.url, 'extra': self.extra}