import logs
from extractors.base import Extractor

logger = logs.get_logger('cookie_extractor')


class CookiesExtractor(Extractor):
    async def extract_information(self):
        logger.info('extracting cookie info')
        cookies = await self.browser.get_cookies()
        list(map(lambda x: calc_lifetime(x, self.page.scan_time), cookies))
        return {'cookies': cookies}


def calc_lifetime(cookie, scan_time):
    if cookie['expires'] is None:
        cookie['lifetime'] = -1
    else:
        cookie['lifetime'] = cookie['expires'] - scan_time
    return cookie
