import logging

from extractors.base import Extractor

logger = logging.getLogger('cookie_extractor')


class CookiesExtractor(Extractor):
    async def extract_information(self):
        logger.info('extracting cookie info')
        cookies = await self.browser.get_cookies()
        # timestamp = int(self.page.scan_start.timestamp())
        # for cookie in cookies:
        #     if cookie['session'] or cookie['expires'] is None:
        #         cookie['lifetime'] = -1
        #     else:
        #         cookie['lifetime'] = cookie['expires'] - timestamp
        return {}#{'cookies': cookies}
