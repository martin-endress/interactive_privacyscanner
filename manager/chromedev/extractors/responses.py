import logging

from chromedev.extractors.base import Extractor

logger = logging.getLogger('response_extractor')


class ResponsesExtractor(Extractor):
    async def extract_information(self):
        return {'responses': self.page.response_log}
