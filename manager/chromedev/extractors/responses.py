import logging

from chromedev.extractors.base import Extractor

logger = logging.getLogger('response_extractor')


class CookiesExtractor(Extractor):
    async def extract_information(self):
        logger.info('extracting responses')
