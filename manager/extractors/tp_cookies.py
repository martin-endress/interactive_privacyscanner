import logs
from extractors.base import Extractor

logger = logs.get_logger('fp_cookie_extractor')


class TPCookiesExtractor(Extractor):
    async def extract_information(self):
        logger.info('extracting cookie info')
        cookies = await self.browser.get_cookies1(self.page.url)
        list(map(lambda x: calc_lifetime(x, self.page.scan_time), cookies))
        return {'fp_cookies': cookies}


def calc_lifetime(cookie, scan_time):
    if cookie['expires'] is None:
        cookie['lifetime'] = -1
    else:
        cookie['lifetime'] = cookie['expires'] - scan_time
    return cookie
