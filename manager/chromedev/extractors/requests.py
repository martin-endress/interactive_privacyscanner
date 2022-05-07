import logging

from chromedev.extractors.base import Extractor

logger = logging.getLogger('requests_extractor')


class RequestsExtractor(Extractor):
    async def extract_information(self):
        return {'requests': self.page.request_log}


