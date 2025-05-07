import abc

class BaseParser:

    @abc.abstractmethod
    def parse_search_page(self, text):
        raise (NotImplemented

    @abc.abstractmethod)
    def parse_detail_page(self, text):
        raise NotImplemented