import abc

class BaseParser(abc.ABC):

    @abc.abstractmethod
    def parse_search_page(self, text):
        """Parse search page and return a list of items or requests."""
        pass

    @abc.abstractmethod
    def parse_detail_page(self, text):
        """Parse detail page and return an item."""
        pass